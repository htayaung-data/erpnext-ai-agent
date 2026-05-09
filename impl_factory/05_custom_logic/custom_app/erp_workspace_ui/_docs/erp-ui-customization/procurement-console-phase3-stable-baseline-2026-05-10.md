# Procurement Console Phase 3 Stable Baseline

Baseline name: `Procurement Console Phase 3 Stable Baseline`

Date: `2026-05-10`

Owner manual acceptance: confirmed clean after final Phase 3 UI review.

Latest relevant commit: `a8ab7f01904175ec9feebcec7dcb8552ddb6bca2`

Earlier relevant accepted closure point: `f57803293f3e621ded92cffe5e51a52506b77fd3`

Source branch: `feature/erpnext-ui-design`

Source worktree: `/home/deploy/erp-projects/erpai_project1_erpnext_ui_design`

## Accepted Scope

Procurement Console Phase 3 is accepted as a stable buyer workbench baseline for:

- Procurement Overview.
- Supplier Directory and read-only Supplier Detail.
- Buying Item Directory and read-only Buying Item Detail.
- Purchase Request Directory, Requests To Source, and Purchase Request Review.
- RFQ Directory, RFQs Awaiting Supplier Response, RFQs Partially Quoted, and RFQ Review.
- Supplier Quotation Directory, Supplier Quotations To Compare, Expiring Supplier Quotations, and Supplier Quotation Review.
- Purchase Order Directory and Phase 3 PO follow-up queues: open, pending approval visibility, due soon, overdue, partially received, received not fully billed, and supplier follow-up.
- Purchase Order Follow-up Detail as a productized read-only buyer follow-up page.
- Quote Comparison as a governed read-only buyer comparison surface.
- Shared Procurement list, report, and child/detail shells for Phase 3 pages.
- Governed native create exceptions required for ERPNext buying workflow.

## Accepted Governed Native Exceptions

The following remain accepted Phase 3 governed native exceptions because ERPNext native document workflow tools are still required:

- New Purchase Request.
- New RFQ.
- New Supplier Quotation.
- New Purchase Order.
- Secondary `Open ERP Form` actions where explicitly permission-governed and not used as productized worklist primary row actions.

Allowed native controls inside those governed forms include ERPNext workflow controls such as Save, grid row actions, Get Items From, Tools, Add row, Add multiple, upload/download tools, and document conversion helpers when ERPNext permissions allow them.

## Deferred Scope

The following are not part of this Phase 3 stable baseline and require later owner approval:

- Managed Procurement forms.
- Supplier create/edit and Supplier Master governance.
- Item create/edit and Item Governance.
- Supplier scorecard and supplier performance analytics.
- Warehouse receiving execution.
- Finance billing, payment, settlement, and accounting execution.
- Purchase Order approve/reject/submit/cancel/amend/close shortcuts from productized Procurement pages.
- Item Price mutation.
- Default Supplier mutation.
- Supplier portal or email sending workflow.
- Phase 4 reporting and analytics.

## Validation Evidence

Closure validation requires the following gates:

- `python3 -m compileall erp_workspace_ui`
- `PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'`
- `node --check` for touched JavaScript files, when JavaScript is touched.
- `git diff --check HEAD`
- Docker Procurement Phase 3 smoke for Purchase Manager.
- Docker Procurement Phase 3 smoke for Purchase User.
- Sales freeze protection gate because shared list runtime/CSS had been touched during the accepted Phase 3 UI closure.

Procurement smoke artifact directory:

- `/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/05_custom_logic/custom_app/erp_workspace_ui/ui_smoke/artifacts/procurement-phase3-assurance`

Sales freeze protection artifact from this closure pass:

- `/tmp/sales-freeze-protection-20260509T180451Z`

No JavaScript runtime was touched by this documentation-only closure commit, so no additional `node --check` target was required for the docs commit itself.

## Live Alignment Summary

Before this baseline closure, controlled live alignment had already been performed for approved ERP Workspace UI Phase 3 files needed by the accepted Procurement UI surface. The final UI closure fixes included shared list runtime alignment to live and cache clear only; no live repository commit was made.

Live deployment folder remains an integration/deployment working tree:

- `/home/deploy/erp-projects/erpai_project1`

The clean source of truth remains:

- `/home/deploy/erp-projects/erpai_project1_erpnext_ui_design`

## Remaining Accepted Risks

- Native ERPNext create forms remain governed exceptions until a future Managed Procurement Forms phase.
- Supplier and Item mutation are deferred to later governed master-data phases.
- Procurement shows downstream receipt and billing posture only for buyer visibility; Warehouse and Finance remain the owning consoles for execution.
- Live deployment repository may remain dirty from controlled alignment work and must not be treated as source of truth.
- Sales Console remains frozen and protected; future shared runtime work must continue to run the Sales freeze protection gate.

## Baseline Rule

Do not start Procurement Phase 4 from this baseline until the owner explicitly approves a Phase 4 scope. Future Procurement work must preserve this Phase 3 baseline, use shared components first, and keep Sales Console freeze protection intact.
