# Procurement Console Phase 7D1 Native Escape Closure Baseline - 2026-05-18

## Status

Procurement Console Phase 7D1 is closed as a protected native escape closure baseline. This is not a final Procurement freeze and does not complete future Procurement phases. It records the owner-accepted policy that normal Purchase User and Purchase Manager workflows inside Procurement Console no longer expose native ERP form escape actions.

## Commit Baseline

- Original Phase 7D1 implementation commits: `71f5e0f`, `de891f9`
- Final cleanup commit: `f4b2ddf1864ff3fe60400a0590cbff3bf8b70897`
- Source branch: `feature/erpnext-ui-design`

## Final Policy

- Normal Purchase User and Purchase Manager sessions must not see native ERP form escape actions inside Procurement Console.
- No in-console admin escape is added in this phase.
- Admin native access, if needed, remains outside Procurement Console through standard ERPNext Desk permissions and navigation.
- Productized Procurement routes remain the supported workspace entry points.
- Future native escape additions require owner approval and an updated protection baseline.

## Protected Pages

The closure baseline protects the absence of normal-user native form escape actions on these surfaces:

- Supplier Detail
- Buying Item Detail
- Purchase Request Review
- RFQ Review
- Supplier Quotation Review
- Saved managed Purchase Request
- Saved managed RFQ
- Saved managed Supplier Quotation
- Saved managed Purchase Order

## Labels Confirmed Absent

Focused Phase 7D1 validation confirmed these labels are not visible inside the protected Procurement Console surfaces for normal Purchase Manager and Purchase User roles:

- `Open ERP Form`
- `Open ERP Supplier Form`
- `Open ERP Item Form`
- `Advanced ERP Form`

## Productized Actions Preserved

The cleanup did not remove accepted productized Procurement actions. These remain protected and expected where the route and permissions allow them:

- Back and Refresh
- Review Request, Review RFQ, Review Quotation, and Review Purchase Order navigation
- RFQ Preview, RFQ PDF, RFQ readiness posture, and disabled/deferred Send RFQ state
- Purchase Order Preview and Purchase Order PDF

## Runtime Cleanup Scope

The final cleanup removed dead generic native chrome helper code from Procurement frontend files after the backend stopped sending native form targets and active dispatch no longer used the helper path. The cleanup did not add new UI, new business behavior, or new native escape routes.

Active runtime static checks after cleanup require zero matches for native escape strings and raw form routes in active Procurement runtime sources, including `Open ERP Form`, `Open ERP Supplier Form`, `Open ERP Item Form`, `Advanced ERP Form`, `native_chrome`, raw `set_route('Form')` or `set_route("Form")`, `/desk/Form/`, and `/app/`.

## Validation Artifacts

- Focused Phase 7D1 source smoke: `/tmp/procurement-phase7d1-cleanup-focused-source-20260518T035652Z`
- Source Sales freeze gate: `/tmp/procurement-phase7d1-cleanup-sales-freeze-20260518T035727Z`
- Source protected workspace gate: `/tmp/procurement-phase7d1-cleanup-protected-workspaces-20260518T040121Z`
- Live alignment hashes: `/tmp/procurement-phase7d1-cleanup-live-align-20260518T041757Z/source-live-hashes.txt`
- Focused Phase 7D1 live smoke: `/tmp/procurement-phase7d1-cleanup-focused-live-20260518T041812Z`
- Post-live protected workspace gate: `/tmp/procurement-phase7d1-cleanup-protected-post-live-20260518T041855Z`
- Post-live Sales freeze gate: `/tmp/procurement-phase7d1-cleanup-protected-post-live-20260518T041855Z/sales-freeze-protection`

## Explicit Deferrals

This baseline does not implement or approve:

- Supplier edit
- Item buying-context edit
- Submit, approval, or conversion workflows
- Receive, bill, or payment workflows
- RFQ or PO send
- Item Price mutation
- Default Supplier mutation
- Contact, User, or portal creation

## Future Change Rule

Any future Procurement phase, shared runtime change, or workspace-wide shell change must preserve this baseline unless the owner explicitly approves a policy change. If a future task needs a governed native escape, the change must update this document or a successor baseline, extend static and browser protection, and pass the protected workspace gate before source commit or live alignment.
