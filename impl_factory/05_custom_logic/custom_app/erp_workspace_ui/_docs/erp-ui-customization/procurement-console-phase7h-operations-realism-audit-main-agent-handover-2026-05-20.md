# Phase 7H Procurement Operations Realism Audit - Main Agent Handover

Date: 2026-05-20
Branch verified: `feature/erpnext-ui-design`
Accepted baseline verified: `84c248256db5a249a92c33e129509ec339a94128`
Reviewer role: ERP Operations Reviewer
Scope of this handover: audit/design guidance only. No runtime implementation is included in this file.

## 1. Read This First

The Procurement Console is safer and more coherent after native ERPNext form escape closure, Supplier Buying Profile, Buying Item Procurement Context, Manager Readiness, and page-level readiness cards. The most important remaining business realism issue is not missing UI polish. It is the readiness model.

The current implementation treats missing Supplier and Item readiness profiles as warnings by default. That is operationally unrealistic for records that already have RFQs, Supplier Quotations, Purchase Orders, Item Supplier rows, Item Price rows, or purchase history. It makes the new readiness feature look as though the business must manually re-certify every historical supplier and item from zero.

The next implementation should not add send, submit, conversion, award, approval, receiving, billing, payment, Item Price mutation, Default Supplier mutation, Item Supplier mutation, Contact/User/portal creation, or AI intake. The next implementation should make readiness history-aware and exception-oriented.

Recommended next phase:

`Phase 7H1: Readiness Inference And Exception Queue Realism`

## 2. Controller Verification Summary

Source gate was run before this handover was requested.

Verified facts:

| Check | Result |
| --- | --- |
| Branch | `feature/erpnext-ui-design` |
| HEAD | `84c248256db5a249a92c33e129509ec339a94128` |
| Accepted baseline ancestor check | Passed, HEAD is the accepted baseline commit |
| Working tree | Clean except known allowed untracked file |
| Allowed untracked file | `ui_smoke/sales_final_acceptance_audit.js` |

A standalone document named `Controller Verification Contract V3` was not found in the repository. The verification approach used here follows the controller contract discipline referenced in prior baselines: source gate first, baseline reading, source inspection, read-only live data inspection, no mutation, and final status confirmation.

## 3. Main Conclusion For The Main Agent

The current readiness layer is valuable, but it is too literal. It sees absence of a custom readiness profile and reports that as a readiness issue. Real procurement operations do not work that way. If a supplier has historical RFQs, quotations, orders, and contact email, the buyer does not normally treat that supplier as unknown just because a new custom profile record was not created yet.

The system needs a distinction between these concepts:

| Concept | Meaning | Should be treated as approval? |
| --- | --- | --- |
| Manual readiness | A Purchase Manager explicitly reviewed a Supplier or Item profile. | Yes, within the productized readiness scope only. |
| Historical trading evidence | The Supplier or Item has prior procurement records. | No. It is evidence of operational familiarity, not formal approval. |
| Communication readiness | Supplier recipient/contact/email/outgoing email readiness for RFQ send. | No. It only affects future governed send readiness. |
| Document action readiness | Whether a PR/RFQ/SQ/PO is prepared for a future lifecycle action. | No. Actions remain deferred until governed workflows exist. |
| Master-data approval | Supplier, Item, Item Price, Default Supplier, Item Supplier, accounting, tax, bank, portal, or user governance. | Not owned by the current Procurement Console. |

Do not interpret this audit as saying all historical suppliers/items are approved. The recommendation is narrower: historical activity should prevent noisy `Not reviewed` warnings, but it must not unlock lifecycle actions or master-data mutation.

## 4. Live Data Evidence

Read-only live data inspection was performed against the running ERPNext site in the backend container. No data was changed.

Observed live signals:

| Signal | Count |
| --- | ---: |
| Suppliers total | 7 |
| Suppliers disabled | 0 |
| Suppliers with RFQ history | 7 |
| Suppliers with Supplier Quotation history | 7 |
| Suppliers with Purchase Order history | 6 |
| Suppliers with any RFQ/SQ/PO buying history | 7 |
| Supplier readiness profiles | 2 |
| Historical suppliers without readiness profile | 5 |
| Suppliers with linked contact | 7 |
| Suppliers with linked contact email | 7 |
| Suppliers with direct Supplier email field populated | 0 |
| Purchase-enabled items | 57 |
| Disabled purchase-enabled items | 0 |
| Items with RFQ history | 9 |
| Items with Supplier Quotation history | 7 |
| Items with Purchase Order history | 29 |
| Items with Item Supplier rows | 6 |
| Items with buying Item Price rows | 44 |
| Items with any RFQ/SQ/PO buying history | 29 |
| Item buying profiles | 3 |
| Historical items without item buying profile | 26 |
| No-history purchase items without profile | 28 |

Operational interpretation:

- All current suppliers have trading evidence, but most do not have the new custom readiness profile.
- All suppliers have contact-email evidence through linked Contacts, so a blanket supplier-level email readiness warning would be misleading.
- Many items have buying history and Item Price evidence, but most historical items do not have a new item buying profile.
- There is also a real population of purchase-enabled items with no history and no profile. Those are the records that should receive true manager review warnings.

## 5. Current Implementation Behavior Observed

Relevant source areas inspected:

- `erp_workspace_ui/procurement_console/readiness.py`
- `erp_workspace_ui/procurement_console/supplier_readiness.py`
- `erp_workspace_ui/procurement_console/item_buying_profile.py`
- `erp_workspace_ui/procurement_console/document_output.py`
- `erp_workspace_ui/procurement_console/service.py`
- `erp_workspace_ui/procurement_console/suppliers.py`
- `erp_workspace_ui/procurement_console/supplier_detail.py`
- `erp_workspace_ui/procurement_console/items.py`
- `erp_workspace_ui/procurement_console/worklist.py`
- `erp_workspace_ui/procurement_console/document_reviews.py`
- `erp_workspace_ui/procurement_console/purchase_order_detail.py`
- `erp_workspace_ui/public/js/procurement_console/procurement_readiness_ui.js`
- Procurement managed form JS files and review page JS files

Current key behaviors:

| Area | Current behavior | Operational concern |
| --- | --- | --- |
| Supplier readiness context | Missing profile becomes warning: `Supplier profile not reviewed`. | Historical suppliers are treated like unknown suppliers. |
| Supplier directory chip | Missing profile displays `No profile`. | Correct technically, but not business-realistic for known suppliers. |
| Supplier statuses | `Ready`, `Needs email`, `Needs contact review`, `Hold for sourcing`, `No profile`. | `Needs email` mixes general supplier readiness with RFQ communication readiness. |
| Item readiness context | Missing profile defaults to `Not reviewed`. | Historical items are treated like new catalog items. |
| Item directory chip | Missing profile displays `Not reviewed`. | Creates noise for items with purchase history. |
| Manager Readiness | Uses recently modified visible suppliers/items/documents and reports first 24 issues. | This is not a true exception queue. It is a sampled warning list. |
| RFQ send readiness | Reads supplier profile status, contact/email sources, outgoing email, and always returns `can_send: false`. | Safe. Keep send disabled. Separate communication issues from buying readiness. |
| Readiness cards | Show document-level issues and deferred future actions. | Useful, but warnings become noisy if history is ignored. |
| Native form routes | Normal Procurement paths do not expose raw ERPNext form links. | Correct. Keep protected. |

## 6. What The Main Agent Must Not Misunderstand

This audit is not recommending any of the following:

- Do not auto-create Supplier Buying Profile records for every historical supplier.
- Do not auto-create Item Buying Profile records for every historical item.
- Do not mark historical records as formally manager-approved.
- Do not treat an RFQ, SQ, PO, Item Price, or Item Supplier row as permission to mutate master data.
- Do not reopen native ERPNext Supplier or Item forms.
- Do not enable RFQ send because contact email exists.
- Do not enable submit, approval, award, conversion, PO release, receive, bill, or pay.
- Do not write Item Price, Default Supplier, Item Supplier, Contact, User, portal, Communication, or Email Queue records.
- Do not treat missing direct `Supplier.email_id` as a supplier readiness failure if linked Contact email exists.
- Do not re-audit managed form autocomplete placement unless a new uncovered page or state is found.

The recommendation is to compute a better read-only readiness display and exception model.

## 7. Recommended Readiness Model

Implement a layered readiness model with explicit precedence.

### 7.1 Precedence Order

Use this order when computing readiness display and manager queue issues:

1. Disabled ERP record or visibility restriction.
2. Manual `Hold for sourcing` from productized profile.
3. Manual profile states from Purchase Manager.
4. Inferred operational history.
5. New/no-history/no-profile state.
6. Communication-only readiness issues.
7. Deferred lifecycle guidance.

### 7.2 Supplier Readiness States

Recommended supplier states:

| State | Source | Tone | Queue behavior | Meaning |
| --- | --- | --- | --- | --- |
| `Hold for sourcing` | Manual Supplier Buying Profile | Critical | Always show | Manager intentionally blocked sourcing use. Overrides history. |
| `Reviewed for buying` or current `Ready` | Manual Supplier Buying Profile | Good | Do not show as issue | Manager reviewed the supplier for buying context. |
| `Needs supplier review` | Manual Supplier Buying Profile | Warning | Show | Manager marked supplier as needing review. |
| `Known trading record` | Inferred RFQ/SQ/PO history, no manual profile | Neutral or good-neutral | Do not show as warning by default | Supplier is not unknown; history exists. Not formal approval. |
| `New supplier - review needed` | No manual profile and no history | Warning | Show | Supplier appears new to buying operations. |
| `Disabled` | ERPNext Supplier | Critical or disabled | Show if used in active docs | Supplier is globally disabled; do not treat as ready. |

Avoid using `No profile` as the main user-facing label for suppliers with history. It is an implementation detail.

### 7.3 Item Readiness States

Recommended item states:

| State | Source | Tone | Queue behavior | Meaning |
| --- | --- | --- | --- | --- |
| `Hold for sourcing` | Manual Buying Item Context | Critical | Always show | Manager intentionally blocked sourcing use. Overrides history. |
| `Reviewed for buying` or current `Ready for buying` | Manual Buying Item Context | Good | Do not show as issue | Manager reviewed procurement context. |
| `Needs sourcing review` | Manual Buying Item Context | Warning | Show | Item needs sourcing review. |
| `Existing buying activity` | Inferred RFQ/SQ/PO history, no manual profile | Neutral or good-neutral | Do not show as warning by default | Item has been bought or sourced before. Not formal price/default supplier approval. |
| `Catalog evidence found` | Item Supplier or buying Item Price exists, but no transaction history | Neutral | Optional queue exclusion or low-priority info | Procurement evidence exists, but not a trading record. |
| `New item - review needed` | Purchase item with no manual profile and no buying evidence | Warning | Show | Item needs manager buying context review. |
| `Disabled` | ERPNext Item | Critical or disabled | Show if used in active docs | Disabled item should not be used in new sourcing/order work. |

Avoid using `Not reviewed` for items with actual buying history.

### 7.4 Communication Readiness

Supplier email/contact readiness should be scoped to RFQ communication, not general supplier readiness.

Rules:

- Missing direct Supplier email is not a supplier buying readiness problem if linked Contact email exists.
- Missing all usable recipient email is an RFQ communication readiness issue.
- Invalid recipient email is an RFQ communication readiness issue.
- Outgoing email unavailable is an environment/send readiness issue.
- RFQ send remains disabled even if all recipients are ready.
- Preferred RFQ contact or recipient override can inform future send readiness, but must not trigger Contact/User/portal side effects.

### 7.5 Document Action Readiness

Document readiness cards should say whether the document appears prepared for a future governed step, not whether the step is available now.

Examples:

- PR readiness can show missing item/date/warehouse issues and future sourcing deferral.
- RFQ readiness can show missing suppliers/items and communication readiness, while send remains disabled.
- Supplier Quotation readiness can show missing rates/validity and future award deferral.
- PO readiness can show missing supplier/items/rates/dates/currency and future release/send deferral.

Deferred future action info should not inflate critical/warning exception counts unless there is an actual current data issue.

## 8. Suggested Implementation Shape For Phase 7H1

### 8.1 Add Central Evidence Helpers

Create a small, read-only readiness evidence layer, either inside `readiness.py` or a new helper module such as `readiness_evidence.py`.

Supplier evidence should inspect:

- `Request for Quotation Supplier` joined to `Request for Quotation`.
- `Supplier Quotation`.
- `Purchase Order`.
- `Dynamic Link` + `Contact` / `Contact Email` for communication evidence.
- ERPNext Supplier disabled status.
- Existing `Procurement Supplier Readiness Profile`.

Item evidence should inspect:

- `Request for Quotation Item` joined to `Request for Quotation`.
- `Supplier Quotation Item` joined to `Supplier Quotation`.
- `Purchase Order Item` joined to `Purchase Order`.
- `Item Supplier`.
- buying `Item Price` rows.
- ERPNext Item disabled and purchase-enabled status.
- Existing `Procurement Item Buying Profile`.

Prefer non-cancelled evidence. Stronger evidence should come from submitted or completed procurement documents. Draft-only evidence can be treated as weaker evidence if needed.

### 8.2 Do Not Materialize Inferred Profiles Yet

For Phase 7H1, compute inference dynamically and display it. Do not insert readiness profile records for existing suppliers/items just because history exists.

Reason:

- Auto-created profiles would look like manager approval even though no manager reviewed them.
- Dynamic inference is safer, reversible, and easier to explain.
- Later phases can add an explicit manager action such as `Confirm reviewed for buying` if the owner wants materialized approval.

### 8.3 Update These Read Paths

Likely affected read paths:

| Source | Recommended change |
| --- | --- |
| `supplier_readiness.supplier_readiness_chip` | Return inferred supplier label/tone when no profile exists and history exists. |
| `readiness.get_supplier_readiness_context` | Do not warn on missing profile if supplier has history. Show informational history evidence instead, or no issue. |
| `readiness._supplier_issues_for_document` | Treat manual hold as blocker. Treat historical no-profile supplier as acceptable for readiness guidance. Keep communication checks in RFQ send readiness. |
| `item_buying_profile.item_readiness_chip_from_row` | Return inferred item label/tone when no profile exists and history exists. |
| `item_buying_profile.readiness_chips_for_items` | Batch-load profiles and evidence to avoid N+1 queries in directories. |
| `readiness.get_item_buying_readiness_context` | Do not warn on historical no-profile item. Warn only new/no-history or manual needs-review/hold. |
| `readiness._item_issues_for_document` | Treat manual hold as blocker, no-history/new as warning, historical no-profile as not a blocker. |
| `readiness._visible_manager_issues` | Replace recent-record sampling with actual exception queries grouped by supplier/item/document readiness. |
| `document_output._rfq_supplier_readiness` | Keep recipient/email logic here. Do not use `Needs email` as general supplier readiness. |

### 8.4 Manager Readiness Queue Redesign

Current queue source is too sample-based. It looks at top recently modified suppliers/items/documents and returns the first 24 issues. This can hide true exceptions and show false ones.

Recommended queue groups:

| Group | Include | Exclude |
| --- | --- | --- |
| Supplier holds | Manual supplier `Hold for sourcing`, disabled suppliers used in active buying docs | Historical suppliers with no profile and no manual hold |
| New supplier review | Suppliers with no profile and no buying history | Suppliers with RFQ/SQ/PO history |
| Item holds | Manual item `Hold for sourcing`, disabled items used in active buying docs | Historical items with no profile and no manual hold |
| New item review | Purchase items with no profile and no buying evidence | Items with PO/SQ/RFQ history; optionally items with Item Supplier/Item Price evidence |
| RFQ communication readiness | RFQs with no suppliers, missing/invalid recipient email, outgoing email unavailable | General supplier `No profile` when supplier has history/contact email |
| Document quality blockers | Missing item lines, supplier, quantity, rate, date, currency depending on document type | Informational future-action deferrals |
| Operational follow-up | Overdue POs, due soon POs, expiring SQs, partial receive/billing visibility | Finance/Warehouse execution actions |

The queue should be an exception dashboard, not a checklist of all unprofiled records.

## 9. Page-Level Guidance For Main Agent

| Page | Keep | Change next | Do not add |
| --- | --- | --- | --- |
| Procurement Overview | KPI cards, pipeline, create actions, manager queue | Make Manager Readiness history-aware and exception-based | Native forms, send/submit/convert actions |
| Supplier Directory | Productized Open action and readiness chip | Use `Known trading record` for historical no-profile suppliers | Inline supplier master edit |
| Supplier Detail | Buying profile, related RFQ/SQ/PO/contact context | Split buying readiness from RFQ communication readiness | Contact/User/portal creation |
| Supplier Buying Profile | Manager-only app-owned fields | Rename `Ready` to `Reviewed for buying` if owner accepts; remove `Needs email` from general status | Supplier master fields, bank/tax/payment/defaults |
| Buying Item Directory | Productized item list and readiness chip | Use `Existing buying activity` for historical no-profile items | Inline Item/Item Price/Item Supplier edit |
| Buying Item Detail | Item context, read-only Item Supplier/Item Price/history | Rename card to `Item Buying Context`; show evidence summary | Default Supplier, Item Price, stock/accounting edits |
| Purchase Request Review/Form | Draft entry and read-only review | Avoid warning historical item lines as unreviewed | PR -> RFQ/PO conversion |
| RFQ Review/Form | Supplier Communication preview/PDF/readiness | Keep email issues in RFQ communication section | Send email, native submit, portal side effects |
| Supplier Quotation Review/Form | Quote entry/review and comparison link | Add award readiness later after design | SQ -> PO conversion now |
| Purchase Order Review/Form | Draft PO and output preview | Keep draft/not-commitment warning | PO submit/release/send now |
| PO Follow-up Detail | Receipt/billing visibility only | Keep Warehouse/Finance boundary wording | Receive/bill/pay buttons |
| Reports | Read-only analytics and drilldowns | Later connect exceptions to readiness queue | Hidden mutation actions |

## 10. Copy And Label Recommendations

Recommended label changes:

| Current label | Recommended label | Reason |
| --- | --- | --- |
| `Manager Readiness` | `Readiness Review Queue` or `Manager Review Queue` | More natural business wording. |
| `Buying Procurement Context` | `Item Buying Context` | Current wording is awkward. |
| `No profile` | `Known trading record` when history exists | Avoids implementation leakage. |
| `Not reviewed` | `New item - review needed` when no history exists | More precise and action-oriented. |
| `Ready` | `Reviewed for buying` | Avoids implying external send or formal ERP approval. |
| `Needs email` | `RFQ recipient missing` under communication readiness | Email is communication-specific, not broad supplier readiness. |
| `Future governed step` | Keep but present as info, not a warning | Deferred work should not look like a defect. |

Also fix the visible `?` separator in readiness row source text from `procurement_readiness_ui.js`. It appears to be intended as a separator between group label and source. Use a neutral separator such as `-` or `:`.

## 11. Governance Requirements

Phase 7H1 must remain read-only except for existing already-approved profile edit behavior.

Allowed for Phase 7H1:

- Read RFQ/SQ/PO/Item Supplier/Item Price history.
- Read Supplier/Item disabled status.
- Read Contact and Contact Email evidence.
- Compute inferred display labels dynamically.
- Update UI copy and readiness classification.
- Add tests/smokes for inference and queue behavior.

Forbidden for Phase 7H1:

- No native ERPNext form links.
- No Supplier master mutation.
- No Item master mutation.
- No Item Supplier mutation.
- No Item Price mutation.
- No Default Supplier mutation.
- No Contact/User/portal creation or mutation.
- No Communication or Email Queue creation.
- No RFQ send/email.
- No submit, approval, rejection, cancel, amend, award, or conversion.
- No Purchase Receipt, Purchase Invoice, Payment Entry mutation.
- No AI intake.
- No Sales Console changes unless shared runtime changes require protected verification.

## 12. Test Strategy For Phase 7H1

Unit tests should cover these cases:

| Test case | Expected result |
| --- | --- |
| Supplier has RFQ/SQ/PO history, no readiness profile | Display `Known trading record`; no general supplier warning. |
| Supplier has no history, no readiness profile | Display review-needed warning. |
| Supplier has history and manual `Hold for sourcing` | Critical hold issue overrides history. |
| Supplier has linked Contact email but no direct Supplier email | No general supplier email warning; RFQ communication can resolve recipient. |
| RFQ supplier has no usable recipient email | RFQ communication readiness warning; `can_send` remains false. |
| Item has PO/SQ/RFQ history, no item profile | Display `Existing buying activity`; no general item warning. |
| Purchase-enabled item has no history and no profile | Display review-needed warning. |
| Item has history and manual `Hold for sourcing` | Critical item hold issue overrides history. |
| Manager queue with historical no-profile records | Does not list them as warning exceptions. |
| Manager queue with manual holds/new no-history records | Lists them in correct groups. |
| Deferred send/submit/conversion messages | Info only, not critical/warning blockers. |

Smoke/protection requirements for implementation:

- Focused Procurement readiness smoke for Supplier Directory, Supplier Detail, Buying Item Directory, Buying Item Detail, Overview Manager Queue, PR/RFQ/SQ/PO readiness cards.
- Static native escape scan remains clean: no `Open ERP Form`, `Open ERP Supplier Form`, `Open ERP Item Form`, `Advanced ERP Form`, `/desk/Form`, `/app/`, or `frappe.set_route("Form"...)` normal-role path.
- Static send-removal scan remains clean: no active SMTP/send endpoint introduced.
- Python unit tests pass.
- JavaScript syntax checks pass for touched JS.
- `git diff --check HEAD` passes.
- Full protected workspace gate if runtime/shared UI files are touched.
- Sales freeze gate if shared runtime or Sales-shared assets are touched.

## 13. Suggested Phase 7H1 Acceptance Criteria

Phase 7H1 should be accepted only if all of these are true:

1. Historical suppliers without profiles no longer appear as generic `No profile` warnings.
2. Historical items without profiles no longer appear as generic `Not reviewed` warnings.
3. New/no-history suppliers and items still require manager review.
4. Manual `Hold for sourcing` overrides all inferred history.
5. Missing email/contact is shown under RFQ communication readiness, not broad supplier buying readiness.
6. Manager Readiness queue becomes an exception queue, not a recently modified sample list.
7. Directory chips, detail summaries, document readiness cards, and manager queue use consistent labels.
8. No forbidden lifecycle/master-data/send behavior is introduced.
9. Existing managed form autocomplete placement is not regressed.
10. Sales Console remains frozen/protected.

## 14. Industry Basis

The recommendation aligns with common ERP procurement patterns:

- ERPNext separates Supplier, Item, Material Request, Request for Quotation, Supplier Quotation, Purchase Order, Purchase Receipt, and Purchase Invoice responsibilities. Supplier and Item records have broader master-data consequences than buyer readiness notes.
- ERPNext RFQ/contact/email behavior can trigger supplier communication and portal side effects in native flows, so RFQ send must remain governed and disabled until explicitly approved.
- SAP, Oracle, Microsoft Dynamics 365, and Odoo all distinguish supplier qualification/master data from day-to-day sourcing and purchasing execution.
- Mature ERP workspaces use exception queues and role-based readiness, not raw master-data form escape as the normal buyer path.

Useful official references for the implementation agent:

- ERPNext Supplier: https://docs.frappe.io/erpnext/user/manual/en/supplier
- ERPNext Item: https://docs.frappe.io/erpnext/user/manual/en/item
- ERPNext Request for Quotation: https://docs.frappe.io/erpnext/user/manual/en/request-for-quotation
- ERPNext Supplier Quotation: https://docs.frappe.io/erpnext/user/manual/en/supplier-quotation
- ERPNext Purchase Order: https://docs.frappe.io/erpnext/user/manual/en/purchase-order
- SAP supplier lifecycle: https://help.sap.com/docs/strategic-sourcing/managing-suppliers-and-supplier-lifecycles/managing-suppliers-and-supplier-lifecycles
- Oracle Supplier Model: https://docs.oracle.com/en/cloud/saas/procurement/26a/oaprc/oracle-supplier-model.html
- Microsoft Dynamics 365 procurement overview: https://learn.microsoft.com/en-us/dynamics365/supply-chain/procurement/procurement-sourcing-overview
- Odoo Purchase: https://www.odoo.com/documentation/19.0/applications/inventory_and_mrp/purchase.html

## 15. Owner Decisions Needed Before Implementation

The Main Agent should ask the owner to decide these before coding if not already decided:

1. Preferred supplier inferred label: `Known trading record`, `Operational history found`, or another phrase.
2. Preferred item inferred label: `Existing buying activity`, `Known buying history`, or another phrase.
3. Should inferred history require submitted/non-cancelled documents only, or should draft records count as weaker evidence?
4. Should Item Supplier and Item Price rows count as enough to suppress `New item - review needed`, or only as `Catalog evidence found`?
5. Should `Ready` be renamed to `Reviewed for buying` in profile status options?
6. Should `Needs email` be removed from Supplier Buying Profile status options and replaced by RFQ communication-only warnings?
7. Should inferred readiness be dynamic only for now, or later confirmable into explicit profile records?
8. Should Manager Readiness show all exceptions with pagination/drilldown or only top grouped exceptions with counts?
9. Should historical evidence age out after a configured period, for example no PO/SQ/RFQ activity in 24 months?
10. Should disabled suppliers/items appear in directories by default or only when the Status filter includes disabled records?

## 16. Recommended Roadmap After Phase 7H1

| Phase | Recommendation |
| --- | --- |
| 7H1 | Implement history-aware readiness inference and exception queue cleanup. |
| 7H2 | Add explicit manager review/override workflow if owner wants formal readiness approval. |
| 7H3 | Design supplier contact/email maintenance request flow without creating Contact/User/portal records directly. |
| 7H4 | Add Quote Comparison next-step readiness and award recommendation design. |
| 7H5 | Design PR -> RFQ, PR -> PO, and SQ -> PO governed conversion before implementation. |
| 7H6 | Implement governed RFQ send only after email infrastructure and owner policy approval. |
| Later | AI Supplier Quotation intake, Quick Find implementation, supplier portal readiness, advanced exception dashboards. |

## 17. Final Instruction To Main Agent

Start with the readiness model, not with new workflow actions. The owner concern is specifically about operational realism: historical suppliers and items should not create a fake backlog of manual readiness work. Solve that first, while preserving the hard governance boundaries already accepted in earlier phases.
