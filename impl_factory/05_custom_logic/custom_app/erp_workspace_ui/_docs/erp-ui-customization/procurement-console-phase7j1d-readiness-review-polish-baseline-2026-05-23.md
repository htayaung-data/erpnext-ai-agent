# Procurement Console Phase 7J1D Readiness Review Polish Baseline

Date: 2026-05-23
Branch: `feature/erpnext-ui-design`
Accepted commit: `88b144263f594f98e6828d52628b5d1983dd7e62`
Baseline type: protected docs-only closure after accepted runtime implementation

## 1. Status

Phase 7J1D is closed as a protected baseline for the Procurement Overview Readiness Review evidence correction and premium polish.

Owner and Main Agent manual/visual review accepted the implementation at commit `88b144263f594f98e6828d52628b5d1983dd7e62`. This document records the accepted evidence and operating contract. It does not introduce runtime, smoke, test, data, or live changes.

## 2. Closure Summary

The earlier Readiness Review Queue showed `21 item buying warnings need review`. That count was too high because some items already had operational sales or purchase evidence and should not be treated as no-history items.

The corrected evidence audit and implementation changed the live queue from 21 warnings to 11 valid item buying warnings.

Accepted behavior:

- Submitted Sales Order, Delivery Note, and Sales Invoice item history counts as operational readiness evidence.
- Submitted Purchase Receipt and Purchase Invoice item history counts as operational buying evidence.
- Items with that operational evidence clear the generic new/no-history warning.
- Remaining warnings are limited to items that still have no buying profile and no qualifying sales or purchase evidence.
- The Readiness Review clear categories render as compact status pills.
- The primary `Review all issues` action is visually stronger.
- The Readiness Review subtitle is left aligned.
- Purchase User still sees no Manager Readiness section and makes zero readiness API calls.
- Readiness remains asynchronous and does not return to the Overview bootstrap payload.

Operational evidence is not formal manager approval. It only prevents the system from treating already-used items as newly registered/no-history items.

## 3. Item Evidence Correction

Corrected audit artifact:

- `/tmp/procurement-readiness-item-sales-audit-20260523T105141Z`

Audit result:

- Original warnings reviewed: 21.
- Items with submitted sales history: 8.
- Additional items with purchase receipt/invoice evidence: 2.
- Valid no-history warnings after correction: 11.

The corrected queue now surfaces true review exceptions instead of mixing known operational items into the warning backlog.

Protected labels:

| Evidence | Readiness label | Queue behavior |
| --- | --- | --- |
| Buying profile exists and is reviewed | `Reviewed for buying` | No warning |
| RFQ, Supplier Quotation, Purchase Order, Purchase Receipt, or Purchase Invoice history | `Existing buying activity` | No generic new-item warning |
| Sales Order, Delivery Note, or Sales Invoice history | `Existing sales activity` | No generic new-item warning |
| Item Supplier or buying Item Price evidence only | `Catalog evidence found` | No high-priority warning |
| No profile and no qualifying operational evidence | `New item - review needed` | Warning |

## 4. Readiness Review UI Baseline

Accepted premium polish:

- Clear categories no longer render as competing cards.
- Clear categories render as compact green status pills:
  - `Supplier readiness clear`
  - `RFQ communication clear`
  - `Document quality clear`
  - `Order follow-up clear`
- Active item buying warnings remain the visual focus.
- The primary action remains `Review all issues`.
- The subtitle remains business-facing and left aligned.
- Expanded/collapsed behavior remains inside the productized Procurement Overview route.

The queue must continue to avoid implementation-language presentation such as raw native routes or internal diagnostic wording.

## 5. Performance Baseline

Live performance evidence:

- `/tmp/procurement-readiness-sales-history-live-performance-20260523T122317Z`

Accepted values from the live performance smoke:

- Manager bootstrap median: `83ms`, max: `105ms`.
- Manager readiness endpoint median: `327ms`, max: `338ms`.
- Manager first useful render at `1136x768`: max `1092ms`.
- Manager readiness ready at `1136x768`: max `1437ms`.
- Purchase User bootstrap median: `65ms`, max: `143ms`.
- Purchase User readiness API calls: `0`.

The Overview bootstrap must continue to exclude `manager_readiness`; Manager Readiness must remain async and local to the Readiness Review widget.

## 6. Validation Evidence

Accepted source/runtime evidence:

- Live focused readiness smoke: `/tmp/procurement-readiness-sales-history-live-smoke-20260523T122232Z`
- Live performance smoke: `/tmp/procurement-readiness-sales-history-live-performance-20260523T122317Z`
- Post-live protected workspace gate: `/tmp/procurement-readiness-sales-history-protected-live-20260523T122410Z`
- Post-live protected workspace summary: `/tmp/procurement-readiness-sales-history-protected-live-20260523T122410Z/protected-workspace-gate-summary.json`

Post-live protected gate status:

- Overall status: pass.
- Head commit: `88b144263f594f98e6828d52628b5d1983dd7e62`.
- Sales freeze inside protected gate: pass.
- Procurement protected stages: pass.
- Artifact stale/failure check: pass.

Source validation for closure:

- Python compileall passed during implementation and protected gate validation.
- Python unit discovery passed with 221 tests after the evidence correction.
- Node syntax checks passed for touched runtime and smoke files during implementation validation.
- `git diff --check HEAD` passed.
- Static native escape, send-removal, and lifecycle/conversion forbidden scans passed.

## 7. Source / Live Hashes

The accepted runtime source/live hashes after live alignment were:

| File | SHA-256 |
| --- | --- |
| `erp_workspace_ui/procurement_console/readiness.py` | `58518b291432faaca33427c8a136ebba758978bc016771bddb36df9e2ae85539` |
| `erp_workspace_ui/procurement_console/readiness_evidence.py` | `ae92ac2965ba35bf56c24ba188cd812051bfecda01143eac89e7f515e27ad001` |
| `erp_workspace_ui/public/js/procurement_console/procurement_readiness_ui.js` | `89e8378ffb46f3249b622ab71a61549361f77c6ed99af03f3a0bb2a7fe2634c3` |

## 8. Protected Behavior Contract

Future changes must preserve:

- The Readiness Review warning count must not include items with qualifying submitted sales or purchase history.
- Operational history labels are evidence labels only, not formal approval or mutation.
- Purchase User must not see Manager Readiness and must not call the manager readiness endpoint.
- Overview bootstrap must not include `manager_readiness`.
- Clear categories must remain compact and low-noise.
- `Review all issues` must remain visually distinct as the primary readiness action.
- Expansion must stay on `/desk/procurement-console` and must not introduce duplicate shell/header/sidebar.
- Productized item review routes must remain productized Procurement routes.

## 9. Forbidden / Deferred Scope

Phase 7J1D did not introduce or start:

- Sales runtime changes.
- Native ERP form escape.
- RFQ or PO send.
- Email/SMTP runtime.
- Communication or Email Queue creation.
- Contact, User, or portal creation.
- Submit, approval, rejection, cancel, amend, or conversion lifecycle actions.
- Receiving, billing, or payment mutation.
- Item Price mutation.
- Default Supplier mutation.
- Item Supplier mutation.
- AI intake.
- Phase 7J2 Supplier Detail or Buying Item Detail redesign.

## 10. Manual Check Instructions

As Purchase Manager:

1. Open Procurement Overview.
2. Confirm the Readiness Review shows `11 item buying warnings need review`.
3. Confirm the clear categories render as compact pills and do not compete with the active warning group.
4. Confirm `Review all issues` is visually stronger than row-level `Review item` buttons.
5. Expand the queue and confirm the route remains `/desk/procurement-console`.

As Purchase User:

1. Open Procurement Overview.
2. Confirm Manager Readiness is absent.
3. Confirm no readiness API call is made by the Purchase User overview smoke/performance evidence.

## 11. Recommended Next Task

Recommended next implementation task:

`Phase 7J2 Supplier Detail and Buying Item Detail tabbed information architecture redesign`

Phase 7J2 must remain separate from this baseline and must preserve all protected Phase 7J1D behavior.
