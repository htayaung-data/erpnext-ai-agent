# Warehouse Console Phase W10 Operations Review And Phase Boundary

Date: 2026-05-30

Branch: `feature/erpnext-ui-design`

Status: docs-only main-control review and phase boundary decision. This document does not implement Warehouse runtime, routes, APIs, tests, smokes, package scripts, or live alignment.

## 1. Baseline Reviewed

Accepted Warehouse runtime baseline before W10:

- W3 read-only foundation: `368dc645e1ce6a6c80849c3cb211c06ade790d7a`
- W3A protected landing closure: `cca15a5fca07ad9bfc4e116101e08536880d8e62`
- W4A inbound receiving visibility: `2a22c1fc9dafe09ca8c62beb04dad69cdb0202ca`
- W4B receiving review: `0abed2f826b14909ec59182f126bdca5ebabf5bd`
- W5A/W5B outbound picking visibility and review: `724ccd2e09857c1df4fa85a7b2ec604448538e07`
- W6A stock exceptions: `982edba`
- W6B stock exception review: `edd9c7e`
- W7A stock posture review: `8ce0961`
- W8A movement visibility: `c408b85b9f9bdab9ac66e0be375930e50a8bece3`
- W8B movement review: `fb337a26d75af22d130fcb0bf43b779794bde055`
- W8B smoke hardening: `20f6fbf3dc0c333f0e2381750f51ace8e0be8ecc`
- W8C transfer visibility: `97cf78485ba5c1cf371dcce8348bab222755df37`
- W9A cockpit information architecture: `97b7f063a8ec9f248e6aaea63a8b5f4444f68336`

Accepted docs and protection artifacts reviewed:

- W8C design plan: `df5f07e257cb0528f67378db9ad242cbd61690c9`
- W8C baseline docs: `386a9d62eeb8e6a58f494fc393eca94d093322f0`
- W9B cockpit usability review: `6e4233fb92cdccfae148193b283e05ed51555105`
- W8C live smoke: `/tmp/warehouse-phase-w8c-live-20260530T124531Z/warehouse-w8c-transfer-visibility-20260530T124535Z/warehouse-w8c-transfer-visibility-summary.json`
- W8C final protected live gate: `/tmp/warehouse-phase-w8c-protected-live-20260530T124609Z/protected-workspace-gate-summary.json`

## 2. Executive Decision

W10 should pause net-new Warehouse feature implementation and run a multi-agent Warehouse protected-surface audit before the next build phase.

Recommended next phase: W10A Multi-Agent Warehouse Protected Surface Audit.

Reason:

- Warehouse now has a complete read-only visibility loop for the first operational tranche:
  - inbound receiving visibility and review;
  - outbound picking visibility and review;
  - stock exceptions and exception review;
  - item/warehouse stock posture review;
  - posted movement visibility and review;
  - warehouse-to-warehouse transfer visibility;
  - protected landing and cockpit information architecture.
- The route surface is no longer small. Future work is more likely to create overlap, duplication, or accidental execution semantics unless the current surface is frozen and audited first.
- The current protected posture is deliberately read-only. Moving toward receiving, picking, transfer, reservation, reconciliation, or stock execution would be a major product/governance shift and should not happen as an incremental UI task.
- The owner has separate Warehouse, Hardening, Security/Stability, and Operation Reviewer agents. W10A should use them as a formal checkpoint, not as ad hoc review after each implementation.

Main-control recommendation:

- Do not assign another Warehouse implementation prompt yet.
- Run W10A as a docs + review + evidence phase across agents.
- Only after W10A is accepted should the owner choose between:
  - W9C/W10B cockpit and mobile polish;
  - a narrow new read-only surface with clear business value;
  - a separately governed execution design track.

## 3. Current Protected Warehouse Surface

Protected top-level route:

- `/desk/warehouse-console`

Protected worklist routes:

- `/desk/warehouse-console-worklist/inbound-receiving`
- `/desk/warehouse-console-worklist/outbound-picking`
- `/desk/warehouse-console-worklist/stock-exceptions`
- `/desk/warehouse-console-worklist/movement-visibility`
- `/desk/warehouse-console-worklist/transfer-visibility`

Protected detail/review routes:

- `/desk/warehouse-console-receiving/<purchase-order>`
- `/desk/warehouse-console-picking/<sales-order>`
- `/desk/warehouse-console-stock-exception/<encoded-context>`
- `/desk/warehouse-console-stock-posture/<encoded-context>`
- `/desk/warehouse-console-movement/<encoded-context>`

Protected role posture:

- Warehouse operational users land in the Warehouse Console.
- Warehouse Manager and Warehouse User/Stock User behavior is covered by focused Warehouse smokes.
- Sales and Procurement protected gates remain mandatory after Warehouse runtime/shared-route changes.

## 4. What Is Now Covered

The accepted Warehouse Console now covers these operational questions:

- What supplier-side receiving work needs review?
- Which purchase orders need receiving posture review?
- What customer-side picking work needs review?
- Which sales orders have picking posture risk?
- Which items or warehouses have stock exception posture?
- What is the item/warehouse stock posture behind a risk?
- What stock movements were posted recently?
- What does a submitted movement mean operationally?
- Which warehouse-to-warehouse transfers were posted and need transfer posture review?
- Where should a Warehouse user start from the cockpit without leaving protected routes?

This is a serious read-only operations visibility foundation. The next question is no longer "what route should we add next?" The next question is "is the protected foundation coherent, safe, and worth freezing before any new capability?"

## 5. Boundary Risks

### 5.1 Execution Drift

Warehouse routes now sit close to real stock operations:

- receiving;
- picking;
- stock exceptions;
- stock posture;
- movement;
- transfer visibility.

The more complete the visibility surface becomes, the easier it is for future prompts to accidentally request verbs like receive, pick, reserve, transfer, issue, post, reconcile, submit, close, or complete. W10A must reaffirm that execution is out of scope unless a new owner-approved execution track is explicitly created.

### 5.2 Surface Overlap

Movement Visibility, Movement Review, Transfer Visibility, and Stock Posture are related. Without a boundary review, future phases may duplicate the same context with different labels.

W10A must check:

- whether Transfer Visibility and Movement Visibility have clear separate purposes;
- whether Stock Posture is a context route, not a generic search surface;
- whether the W9A cockpit routes users to the right view without crowding;
- whether "Needs Review" semantics are consistent across inbound, outbound, exception, movement, and transfer views.

### 5.3 Evidence Quality

W9B already noted that screenshot evidence should distinguish initial cockpit captures from post-navigation captures. W8C improved smoke evidence for transfer visibility. W10A should standardize evidence expectations for all future Warehouse phases.

Required future evidence pattern:

- initial route screenshot;
- direct route reload screenshot;
- drilldown screenshot after custom route navigation;
- mobile/laptop/desktop screenshot where layout changes;
- shell count and duplicate route assertions;
- negative assertions for native escape, lifecycle actions, valuation/commercial exposure, and Quick Find/Search.

### 5.4 Shared Helper And Permission Posture

Security/Stability Review identified a residual risk in the shared Warehouse `_safe_get_list` helper: it has a broad fallback to `frappe.get_all` on exception. W8C remained role-gated and read-gated, but W10A should audit this helper across all Warehouse service methods before more routes depend on it.

W10A should decide whether to:

- keep the helper as accepted with documented constraints;
- harden the helper in a source-only maintenance phase;
- add specific tests around helper fallback behavior and restricted states.

## 6. W10A Multi-Agent Audit Scope

W10A should be a review phase. It may produce docs and, if needed, narrow hardening patches. It should not add new product routes.

### 6.1 Warehouse Agent Role

Warehouse Agent should not implement a new feature in W10A.

Warehouse Agent task:

- Inventory the current Warehouse route families and service methods.
- Confirm each route maps to a real warehouse operational question.
- Identify duplicate concepts, confusing labels, or dead/low-value panels.
- Propose only consolidation or copy/layout improvements.
- Do not add new routes, backend methods, or execution controls.

### 6.2 Hardening Agent Role

Hardening Agent task:

- Audit route idempotency across W3-W8C.
- Audit duplicate shell/header/sidebar behavior.
- Audit stale async response protection across overview, worklists, and detail pages.
- Audit refresh/back/repeated-route behavior.
- Audit mobile/laptop/desktop layout pressure.
- Audit smoke evidence consistency and screenshot naming.
- Propose hardening patches only if they preserve current behavior.

### 6.3 Security And Stability Review Agent Role

Security/Stability Agent task:

- Audit all Warehouse backend methods for read-only posture.
- Audit permission and role gates.
- Audit bounded query posture.
- Audit `_safe_get_list` fallback risk.
- Audit no native ERP route escape.
- Audit no Stock Ledger/Stock Balance/native Stock Entry exposure.
- Audit no valuation/accounting/commercial exposure.
- Audit no server write calls or lifecycle controls.
- Audit Sales/Procurement dirty boundary.

### 6.4 Operation Reviewer Agent Role

Operation Reviewer Agent task:

- Review the full Warehouse flow as a warehouse supervisor:
  - Cockpit;
  - inbound receiving;
  - receiving review;
  - outbound picking;
  - picking review;
  - stock exceptions;
  - stock exception review;
  - stock posture review;
  - movement visibility;
  - movement review;
  - transfer visibility.
- Confirm route names and section labels match warehouse mental models.
- Confirm no route implies execution where none exists.
- Confirm empty states are useful and not technical.
- Confirm current route set is enough for read-only operations visibility or identify the single highest-value missing visibility question.

### 6.5 Main Control Role

Main Control task:

- Sequence the agent reviews.
- Run any required credentialed focused smokes after source patches.
- Run Sales freeze and protected workspace gates if source patches are made.
- Commit/push accepted docs or hardening patches.
- Live-align runtime files only if a patch changes runtime.
- Record W10A baseline decision.

## 7. Proposed W10A Deliverables

W10A should produce:

- A protected Warehouse route/service inventory table.
- A risk register for execution drift, native escape, valuation exposure, and smoke evidence gaps.
- A route consolidation recommendation.
- A copy/label consistency recommendation.
- A hardening recommendation for `_safe_get_list`.
- A decision on whether Warehouse read-only visibility can be frozen as `warehouse-console-readonly-freeze-v1`.
- A decision on the next implementation class:
  - polish only;
  - new read-only visibility only;
  - execution design track;
  - pause Warehouse and move to another workspace.

## 8. Explicitly Deferred Work

Do not start any of these until W10A is complete and owner-approved:

- Receiving execution.
- Picking execution.
- Transfer execution.
- Stock Entry creation/submission/cancel/amend.
- Purchase Receipt creation/submission.
- Delivery Note creation/submission.
- Pick List creation/submission.
- Reservation/unreservation.
- Stock Reconciliation.
- Stock Ledger or Stock Balance exposure.
- Serial/batch assignment.
- Barcode scan workflows.
- Native ERPNext route escape.
- Warehouse Quick Find/Search.
- Valuation/accounting/commercial exposure.
- Contact/User/portal/email/print/AI/workflow approval behavior.

## 9. Recommended Next Prompt

Use this as the next sequential prompt for the Warehouse Agent only after this W10 document is accepted:

```text
You are the Warehouse Agent.

Task: Perform W10A source-aware Warehouse protected-surface inventory and operations fit review. Do not implement a new route or feature.

Repository:
- /home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/05_custom_logic/custom_app/erp_workspace_ui
- Branch: feature/erpnext-ui-design

Authority:
- _docs/erp-ui-customization/warehouse-console-phase-w10-operations-review-and-phase-boundary-2026-05-30.md
- Existing Warehouse baselines W3 through W8C and W9A/W9B.

Review:
- Inventory every Warehouse route, service method, custom drilldown, and smoke.
- Map each route to the operational question it answers.
- Identify overlap, confusing labels, dead panels, weak empty states, or cockpit crowding.
- Confirm no route implies receiving, picking, transfer, reconciliation, reservation, posting, or lifecycle execution.
- Propose only docs/copy/layout/hardening recommendations. Do not add routes or backend methods.

Validation:
- If no source files are changed, report docs/review findings only.
- If a docs-only patch is made, run git diff --check HEAD.
- If any runtime/test/smoke patch is made, stop and ask main control before continuing.

Stop before commit, push, live alignment, or protected gates.

Final report:
- Route/service inventory summary.
- Operational-fit findings.
- Recommended consolidation/polish items.
- Any hard blockers.
- Whether Hardening Agent should proceed.
```

## 10. Main Control Recommendation

Proceed to W10A multi-agent audit.

Do not assign a new feature implementation to Warehouse Agent yet. The Warehouse Console is at a natural review boundary, and the next engineering value is protecting coherence, safety, and evidence quality before increasing capability.
