# Procurement Console Phase 7H1 Readiness Inference And Exception Queue Baseline

Date: 2026-05-20
Branch: `feature/erpnext-ui-design`
Protected baseline HEAD: `ef31911a30f0838fddc7735d17741573a997c70c`
Baseline type: protected documentation closure

## 1. Executive Summary

Phase 7H1 is protected and accepted as the readiness realism baseline for Procurement Console.

Readiness is now history-aware and exception-oriented. Historical suppliers no longer create fake `No profile` warnings just because the custom Supplier Buying Profile does not exist. Historical buying items no longer create fake `Not reviewed` warnings just because the custom Buying Item Procurement Context profile does not exist.

Manager Readiness is an exception queue, not a sampled backlog of recent records. It is expected to surface real holds, new/no-history review needs, RFQ communication readiness issues, and document quality blockers. It must not inflate warning or critical counts with historical no-profile suppliers/items or deferred lifecycle guidance.

RFQ communication readiness remains separate from broad supplier buying readiness. Supplier recipient/email issues belong to RFQ communication readiness; they do not create generic supplier buying backlog.

Send, lifecycle, conversion, receiving, billing, payment, master-data mutation, and native ERP escape behavior remain deferred or forbidden.

## 2. Implemented Readiness Model

Phase 7H1 uses this precedence model when rendering readiness and queue issues:

1. Disabled or visibility-restricted records.
2. Manual `Hold for sourcing` from the productized Supplier Buying Profile or Buying Item Procurement Context.
3. Manual manager profile state.
4. Inferred operational history.
5. New/no-history/no-profile state.
6. Communication-only readiness.
7. Deferred lifecycle info.

Business labels protected by this baseline:

| Situation | Protected label | Queue behavior |
| --- | --- | --- |
| Supplier has RFQ/SQ/PO history and no profile | `Known trading record` | No generic warning |
| Item has RFQ/SQ/PO buying history and no profile | `Existing buying activity` | No generic warning |
| Item has Item Supplier or buying Item Price evidence only | `Catalog evidence found` | Not a high-priority warning |
| Supplier has no profile and no history | `New supplier - review needed` | Warning |
| Item has no profile and no evidence | `New item - review needed` | Warning |
| Manual ready supplier/item profile | `Reviewed for buying` | No issue |
| Deferred send/submit/conversion/award/release | Info only | Does not inflate warning/critical backlog |

Inferred history is operational evidence only. It is not formal manager approval and does not create a custom readiness profile record.

## 3. Supplier Readiness Contract

Manual `Hold for sourcing` overrides all inferred trading history and remains a critical blocker.

Manual Supplier Buying Profile state overrides inference. A manager-reviewed supplier displays the manager-facing business label. Manual non-ready states remain warnings or blockers according to the profile value.

Historical RFQ, Supplier Quotation, or Purchase Order activity suppresses the generic missing-profile warning and displays `Known trading record`. This means the supplier is operationally known, not formally approved.

Missing direct Supplier email is not a broad supplier readiness issue when linked Contact email evidence exists. Email/contact readiness belongs to RFQ communication readiness and future governed send design.

Phase 7H1 does not mutate Supplier master data. It does not create suppliers, contacts, users, portal users, communications, or email queue records.

## 4. Item Readiness Contract

Manual `Hold for sourcing` overrides all inferred item evidence and remains a critical blocker.

Manual Buying Item Procurement Context state overrides inference. A manager-reviewed item displays `Reviewed for buying`; manual review-needed states remain warnings.

RFQ, Supplier Quotation, or Purchase Order item history suppresses the generic not-reviewed warning and displays `Existing buying activity`.

Item Supplier or buying Item Price evidence without transaction history displays `Catalog evidence found`. This is catalog/procurement evidence only, not approval to use or mutate pricing/default supplier records.

A purchase-enabled item with no profile and no buying evidence still displays `New item - review needed` and can appear as a true manager exception.

Phase 7H1 does not mutate ERPNext Item, Item Supplier, Item Price, Item Default, Default Supplier, UOM, valuation, tax, warehouse, reorder, stock, serial/batch, or variant fields.

## 5. Manager Readiness Queue Contract

The Manager Readiness queue shows real exceptions. It excludes historical no-profile suppliers/items unless they are manually held or otherwise blocked.

The queue includes new/no-history review needs and manual holds. It can include RFQ communication readiness and document quality blockers when those checks are relevant.

Deferred lifecycle messages such as future send, submit, conversion, award, release, receive, bill, or pay remain info-only and must not inflate warning/critical backlog counts.

Purchase Manager sees the Overview-level Manager Readiness queue. Purchase User does not see the Overview-level Manager Readiness queue. Purchase User can still see permitted page-level readiness cards where the page itself is accessible.

## 6. UI/UX Contract

The Manager Overview subtitle is now:

`Exception queue with guided fixes`

The subtitle must remain compact and must not wrap awkwardly with a single word on a new line.

Directory chips and detail readiness cards use business labels, not implementation labels. `No profile` and `Not reviewed` must not appear as generic backlog labels for historical suppliers/items.

Readiness cards remain compact and productized. They use guided productized fix paths, not raw ERPNext route names.

Native form labels remain absent from normal Procurement workflows. Managed form autocomplete placement remains protected and should continue opening downward where usable space exists.

## 7. Validation Evidence

Accepted validation evidence:

- Python compileall passed.
- Python unit discovery passed with 218 tests.
- `node --check` passed for touched JavaScript/smoke files during implementation validation.
- `git diff --check HEAD` passed.
- Static native escape scan passed.
- Static send-removal scan passed.
- Lifecycle/conversion forbidden scan passed.
- Focused Phase 7H1 live smoke passed.
- Subtitle polish focused live smoke passed.
- Final focused reports/filter subgate passed.
- Final protected workspace gate passed.
- Sales freeze inside final protected gate passed.
- Owner manual review accepted.
- Controller screenshot review accepted after final subtitle polish and smoke timing stabilization.

Implementation and fix commits included in this baseline:

| Commit | Purpose |
| --- | --- |
| `619cb8b93c8a9d578722fa67cac22276569b2089` | Runtime readiness inference from supplier/item buying history |
| `cd6a3b4d8361891e2550eff9c32b258a0f9f6864` | Focused Phase 7H1 smoke backdrop hardening |
| `fe340ae89e1397a1004e3a7b4c0321dc7e0db165` | Optional readiness evidence permission modal suppression |
| `5bf0b8071007001203adf555fafb82951549846a` | Manager Readiness subtitle polish |
| `ef31911a30f0838fddc7735d17741573a997c70c` | Procurement filter deck gate timing stabilization |

Key runtime source/live hashes accepted for this baseline:

| File | Hash |
| --- | --- |
| `readiness_evidence.py` | `eb9ea9104c49325af0ff92ef5eec7c5b6d854e41ca5b9e9fb5e937b817d63ca4` |
| `readiness.py` | `f7fef92072446da7e2e17cb563ae047bb1852dc4b471a841c9977c69aad8f11b` |
| `procurement_readiness_ui.js` | `67410834398ae5e7e1c738ffb662a484b9bab9646977f8f87d43ce3f308f31c5` |
| `supplier_readiness.py` | `bf68070a52601f62aa9b158744343beec60eaeb6116465d9ec9cb227630a62b9` |
| `item_buying_profile.py` | `cff0de6a1322f5d531eb0c7f9e5d345ab9925739061f60ea55c27812f6702c64` |

## 8. Artifact Paths

Accepted artifact paths:

- Focused Phase 7H1 live smoke: `/tmp/procurement-phase7h1-live-pass-20260520T040738Z/procurement-phase7h1`
- Phase 7H1 focused summary: `/tmp/procurement-phase7h1-live-pass-20260520T040738Z/procurement-phase7h1/phase7h1-summary.json`
- Subtitle polish focused live smoke: `/tmp/procurement-phase7h1-readiness-subtitle-live-20260520T060405Z`
- Final focused reports/filter subgate: `/tmp/procurement-reports-filter-focused-after-smoke-wait-20260520T075451Z`
- Final protected workspace gate: `/tmp/protected-workspaces-20260520T082155Z/protected-workspace-gate-summary.json`
- Sales freeze inside final protected gate: `/tmp/protected-workspaces-20260520T082155Z/sales-freeze-protection/sales-freeze-protection-summary.json`

## 9. Manual Check Instructions

As Purchase Manager:

1. Open Supplier Directory and confirm a historical supplier shows `Known trading record`.
2. Open that Supplier Detail page and confirm no fake no-profile warning appears for the historical supplier.
3. Open Buying Item Directory and confirm a historical item shows `Existing buying activity` or `Catalog evidence found`.
4. Open that Buying Item Detail page and confirm no fake not-reviewed warning appears for the historical item.
5. Open Procurement Overview and confirm Manager Readiness shows real exceptions, not every historical no-profile supplier/item.
6. Confirm the Manager Overview subtitle reads `Exception queue with guided fixes`.
7. Open RFQ Review and confirm Supplier Communication remains separate, Preview/PDF remain available, and Send RFQ remains disabled.
8. Check managed PR/RFQ/SQ/PO form autocomplete placement still opens downward where there is usable space.
9. Confirm no `Open ERP Form`, `Open ERP Supplier Form`, `Open ERP Item Form`, or `Advanced ERP Form` appears.
10. Confirm no active send, submit, convert, approve, receive, bill, or payment action appears.

As Purchase User:

1. Open Procurement Overview and confirm Manager Readiness is absent.
2. Open Supplier Detail and Buying Item Detail pages permitted to the role and confirm readiness cards remain read-only.
3. Confirm no native ERP form escape appears.
4. Confirm RFQ Review still shows communication readiness separately and Send RFQ remains disabled.

## 10. Forbidden / Deferred Scope

Phase 7H1 did not implement or start:

- Native ERP form escape.
- RFQ send/email/SMTP.
- Communication or Email Queue creation.
- Contact/User/portal creation.
- Submit, approval, rejection, cancel, or amend.
- PR-to-RFQ, RFQ-to-SQ, SQ-to-PO, or PR/MR-to-PO conversion.
- Purchase Receipt, Purchase Invoice, or Payment Entry.
- ERPNext Item mutation.
- Item Supplier mutation.
- Item Price mutation.
- Item Default or Default Supplier mutation.
- Supplier master mutation outside already protected Supplier Buying Profile fields.
- Receiving, billing, or payment workflows.
- Stock, accounting, UOM, valuation, tax, reorder, warehouse, serial/batch, or variant changes.
- AI intake.
- Sales runtime changes.

## 11. Remaining Future Roadmap

Recommended next phase: `Phase 7I Full Procurement Freeze Audit` as a design/audit task before starting another capability implementation.

Reason: Supplier readiness, item buying context, native escape closure, RFQ communication readiness, and Manager Readiness have now accumulated several protected layers. A full Procurement freeze audit should confirm the complete workspace contract, route inventory, forbidden-action scans, role matrix, UI consistency, and protected gate coverage before adding another manager action surface.

If the owner prefers a more capability-specific step after the freeze audit, the next design candidate is `Phase 7H2 Explicit Manager Review / Override Workflow Design`. That phase would decide whether inferred history can be formally confirmed by a manager action. It must remain design-only until explicitly approved and must not introduce lifecycle or master-data mutation by default.