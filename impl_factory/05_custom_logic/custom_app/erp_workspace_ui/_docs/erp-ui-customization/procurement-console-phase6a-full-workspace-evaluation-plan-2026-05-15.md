# Procurement Console Phase 6A Full Workspace Evaluation Plan

Date: 2026-05-15

Planning baseline commit: `0e2440d2d530a6eeaa64dfeb87979a6fd3b0c91c`

## Executive Recommendation

Phase 6A is an evaluation and planning baseline after completion of the managed buying form family. No runtime change is approved by this document.

The next implementation sequence should not jump into isolated polish. The recommended sequence is:

- Phase 6B: supplier-facing document output design for RFQ and Purchase Order print/PDF/email/send.
- Phase 6C: supplier-facing document output implementation after Phase 6B approval.
- Phase 6D: full Procurement workspace UI polish/redesign implementation using the page-specific audit plan below.
- Phase 6E or later: conversion workflows once upstream submit/review governance exists.
- Phase 6F or later: operational lifecycle workflows owned with Warehouse and Finance boundaries.

Reason: RFQ and Purchase Order are supplier-facing documents. A buyer can now draft them in managed forms, but the workspace still lacks a designed, governed way to generate supplier-facing output, select recipients, send email, produce PDF/print artifacts, and record communication history. That gap is more business-critical than broad visual redesign, but it must be designed before implementation.

## Baseline Context

Protected managed buying forms:

- Phase 5A: Managed Purchase Request.
- Phase 5B: Managed RFQ.
- Phase 5C: Managed Supplier Quotation.
- Phase 5D: Managed Purchase Order.

Latest protected baseline:

- Phase 5D baseline commit: `0e2440d2d530a6eeaa64dfeb87979a6fd3b0c91c`.

Accepted protection evidence at this baseline:

- Focused Phase 5D smoke: `/tmp/procurement-phase5d-autocomplete-placement-final-20260515T121000Z/procurement-phase5d`.
- Protected workspace gate: `/tmp/protected-workspaces-20260515T120612Z`.
- Sales freeze inside protected gate: `/tmp/protected-workspaces-20260515T120612Z/sales-freeze-protection`.
- Purchase Order form source/live hash: `4835e4f747717890689f1d8754a03cf067658f372b984a0dd03328196903c6ed`.

Baseline rules:

- Sales Console is frozen and protected.
- Managed Purchase Request, RFQ, Supplier Quotation, and Purchase Order forms are protected.
- Native ERP form access remains a governed secondary exception only where explicitly allowed.
- Productized create actions for the four buying documents must route to managed forms, not native ERPNext create pages.
- No Phase 6 implementation is approved by this planning document.

## Route And Surface Inventory

All known Procurement surfaces are classified below. No route is intentionally left unclassified.

### Core Shell

| Surface | Route or source | Classification | Current evidence | Phase 6A status |
| --- | --- | --- | --- | --- |
| Procurement launcher | `/desk/procurement-console-home` | Productized launcher handoff | Protected gate core navigation pass | Protected, no redesign before plan |
| Procurement Overview | `/desk/procurement-console` | Productized overview | Protected gate core navigation pass; create actions covered by Phase 5 smokes | Needs full visual capture in Phase 6D audit |
| Procurement sidebar/navigation | shared Procurement sidebar | Productized navigation | Protected gate core navigation pass | Protected; future changes require Sales freeze if shared runtime touched |
| Procurement search | `search_procurement_console_workspace` | Productized role-scoped search | Source inventory; not screenshot-verified in Phase 6A | Evidence gap, add search smoke/screenshot later |

### Directories And Worklists

| Surface | Route | Classification | Entry/action status | Evidence status |
| --- | --- | --- | --- | --- |
| Suppliers | `/desk/procurement-console-worklist/supplier-directory` | Productized worklist | Rows open Supplier Detail | Narrow filter screenshot exists; full desktop screenshot gap |
| Purchase Requests | `/desk/procurement-console-worklist/purchase-request-directory` | Productized worklist | `New Purchase Request` routes to managed PR form | Phase 5A smoke protected; full page screenshot gap |
| Requests to Source | `/desk/procurement-console-worklist/requests-to-source` | Productized worklist | PR-to-RFQ action deferred unless submitted/governed | Source classified; screenshot gap |
| Purchase Orders | `/desk/procurement-console-worklist/purchase-order-directory` | Productized worklist | `New Purchase Order` routes to managed PO form | Phase 5D smoke protected; full page screenshot gap |
| Purchase Orders Pending Approval | `/desk/procurement-console-worklist/purchase-orders-pending-approval` | Productized worklist | Read/review only, no approval action in managed scope | Source classified; screenshot gap |
| Open Purchase Orders | `/desk/procurement-console-worklist/purchase-orders-open` | Productized worklist | Row drilldown to productized PO detail | Source classified; screenshot gap |
| Late or Unreceived Purchase Orders | `/desk/procurement-console-worklist/purchase-orders-late-or-unreceived` | Productized worklist | Follow-up/read surface | Source classified; screenshot gap |
| Purchase Orders Due Soon | `/desk/procurement-console-worklist/purchase-orders-due-soon` | Productized worklist | Follow-up/read surface | Source classified; screenshot gap |
| Overdue Purchase Orders | `/desk/procurement-console-worklist/purchase-orders-overdue` | Productized worklist | Follow-up/read surface | Source classified; screenshot gap |
| Partially Received Purchase Orders | `/desk/procurement-console-worklist/purchase-orders-partially-received` | Productized worklist | Visibility only, no receiving mutation | Source classified; screenshot gap |
| Purchase Orders Not Billed Visibility | `/desk/procurement-console-worklist/purchase-orders-not-billed-visibility` | Productized worklist | Visibility only, no billing mutation | Source classified; screenshot gap |
| Purchase Orders Supplier Follow Up | `/desk/procurement-console-worklist/purchase-orders-supplier-follow-up` | Productized worklist | Rows open PO Follow-up Detail | PO follow-up detail screenshot exists; list screenshot gap |
| RFQs | `/desk/procurement-console-worklist/rfq-directory` | Productized worklist | `New RFQ` routes to managed RFQ form | Phase 5B smoke protected; full page screenshot gap |
| RFQs Awaiting Supplier Response | `/desk/procurement-console-worklist/rfqs-awaiting-supplier-response` | Productized worklist | Read/follow-up; no send workflow yet | Source classified; screenshot gap |
| RFQs Partially Quoted | `/desk/procurement-console-worklist/rfqs-partially-quoted` | Productized worklist | Read/follow-up; no conversion workflow yet | Source classified; screenshot gap |
| Supplier Quotations | `/desk/procurement-console-worklist/supplier-quotation-directory` | Productized worklist | `New Supplier Quotation` routes to managed SQ form | Narrow filter screenshot and Phase 5C smoke evidence |
| Supplier Quotations To Compare | `/desk/procurement-console-worklist/supplier-quotations-to-compare` | Productized worklist | Quote Comparison entry point | Source classified; screenshot gap |
| Supplier Quotations Expiring | `/desk/procurement-console-worklist/supplier-quotations-expiring` | Productized worklist | Review/compare support | Source classified; screenshot gap |
| Buying Items | `/desk/procurement-console-worklist/buying-item-directory` | Productized worklist | Rows open Item Detail | Narrow filter screenshot exists; full desktop screenshot gap |

### Reports

| Surface | Route | Classification | Evidence | Phase 6A assessment |
| --- | --- | --- | --- | --- |
| Reports Index | `/desk/procurement-console-report` | Productized report index | `/tmp/protected-workspaces-20260515T120612Z/procurement-reports-and-filter-layout-purchase-manager/procurement-reports-index.png` | Protected; should be reviewed in 6D for visual hierarchy and report grouping |
| Quote Comparison | `/desk/procurement-console-report/supplier-quotation-comparison` | Productized report wrapper over ERPNext comparison | Protected gate report pass; no specific final screenshot listed in final gate artifact scan | Business-critical; strengthen screenshot coverage before quote-award work |
| Purchase Order Analysis | `/desk/procurement-console-report/purchase-order-analysis` | Productized report wrapper | `procurement-purchase-order-analysis.png` | Protected; relevant for future PO performance review |
| Demand-to-Order Coverage | `/desk/procurement-console-report/demand-to-order-coverage` | Productized report | `procurement-demand-to-order-coverage.png` | Protected; useful for conversion workflow planning |
| Item Purchase History | `/desk/procurement-console-report/item-purchase-history` | Productized report | `procurement-item-purchase-history.png` | Protected; must stay read-only, no Item Price mutation |

### Detail And Review Pages

| Surface | Route | Classification | Evidence | Phase 6A status |
| --- | --- | --- | --- | --- |
| Supplier Detail | `/desk/procurement-console-supplier/<supplier>` | Productized read/detail page | `supplier-detail-detail-page.png` | Accepted as current surface; likely trails managed-form premium polish |
| Item Detail | `/desk/procurement-console-item/<item>` | Productized read/detail page | `item-detail-detail-page.png` | Accepted as current surface; keep Item Price mutation forbidden |
| Purchase Request Review | `/desk/procurement-console-purchase-request-review/<material-request>` | Productized review page | Protected worklist/detail pass | Productized read/review; conversion remains deferred |
| RFQ Review | `/desk/procurement-console-rfq-review/<rfq>` | Productized review page | Protected worklist/detail pass | Needs future supplier-facing output design integration |
| Supplier Quotation Review | `/desk/procurement-console-supplier-quotation-review/<supplier-quotation>` | Productized review page | Protected worklist/detail pass; compare action classified | Quote Comparison action accepted; PO creation deferred |
| Purchase Order Follow-up Detail | `/desk/procurement-console-po-follow-up/<purchase-order>` | Productized PO detail/follow-up | `po-follow-up-detail-detail-page.png` | Read/follow-up only; output/send and lifecycle actions deferred |

### Managed Forms

| Surface | Route | Classification | Evidence | Baseline status |
| --- | --- | --- | --- | --- |
| Managed Purchase Request | `/desk/procurement-console-purchase-request-form/new`, `/desk/procurement-console-purchase-request-form/<name>` | Protected managed draft form | Phase 5A baseline and protected gate | Protected; internal demand only |
| Managed RFQ | `/desk/procurement-console-rfq-form/new`, `/desk/procurement-console-rfq-form/<name>` | Protected managed draft form | Phase 5B baseline and protected gate | Protected; supplier-facing output missing by design |
| Managed Supplier Quotation | `/desk/procurement-console-supplier-quotation-form/new`, `/desk/procurement-console-supplier-quotation-form/<name>` | Protected managed draft form | Phase 5C baseline and final gate screenshots | Protected; direct offer recording only |
| Managed Purchase Order | `/desk/procurement-console-purchase-order-form/new`, `/desk/procurement-console-purchase-order-form/<name>` | Protected managed draft form | Phase 5D final smoke and baseline | Protected; draft PO only |

### Native Exceptions

| Native path/action | Classification | Current policy |
| --- | --- | --- |
| `Open ERP Form` from saved managed PR/RFQ/SQ/PO | Accepted governed secondary exception | Allowed only after save and only if permissions allow |
| `Open ERP Form` from review/detail pages | Accepted governed secondary exception | Allowed where explicitly declared |
| ERP Supplier Form from Supplier Detail | Accepted governed secondary exception | Secondary manager/write-permission action only |
| ERP Item Form from Item Detail | Accepted governed secondary exception | Secondary governed action only |
| Raw ERPNext create pages for Material Request, RFQ, Supplier Quotation, Purchase Order | Deferred cleanup/governance compatibility entries | Must not be primary productized create actions after Phase 5A-5D |
| Native lifecycle tools such as `Get Items From`, Tools, Save, Add row | Governed native lifecycle exception | Available only in native ERP form context, not as productized managed surface actions |

## Evidence Strategy

Existing evidence sources:

- Final protected gate: `/tmp/protected-workspaces-20260515T120612Z`.
- Focused Phase 5D smoke: `/tmp/procurement-phase5d-autocomplete-placement-final-20260515T121000Z/procurement-phase5d`.
- Phase 5C artifacts inside final protected gate: `/tmp/protected-workspaces-20260515T120612Z/procurement-phase5c-purchase-manager` and `/tmp/protected-workspaces-20260515T120612Z/procurement-phase5c-purchase-user`.
- Report/filter screenshots: `/tmp/protected-workspaces-20260515T120612Z/procurement-reports-and-filter-layout-purchase-manager`.
- Detail screenshots: `/tmp/protected-workspaces-20260515T120612Z/procurement-worklists-and-details-purchase-manager`.
- Autocomplete/link screenshots: `/tmp/protected-workspaces-20260515T120612Z/procurement-autocomplete-and-link-controls-purchase-manager`.

Evidence gaps before any broad redesign implementation:

- Procurement Overview 1136px and 1440px screenshots should be captured explicitly after Phase 5D.
- All directory/worklist pages should have desktop and laptop screenshots, not only narrow filter checks.
- RFQ and Purchase Request managed form final screenshots should be referenced from their final accepted artifacts or recaptured for a complete post-Phase-5 family book.
- Quote Comparison needs explicit final screenshot capture because it is central to supplier-offer workflow.
- Search requires screenshots and API/empty-state evidence.
- Purchase User screenshot coverage should be strengthened for all read-only/detail/report pages.
- Supplier-facing RFQ/PO output does not exist yet, so no output screenshots can be claimed.

Phase 6D should start with a no-code screenshot capture run before changing UI. That capture should include 1136x768 and 1440x900 for every surface in this document.

## UI/UX Findings By Surface

### What Is Already Acceptable And Protected

- Managed PR/RFQ/SQ/PO forms are the strongest Procurement surfaces. They share a protected managed form family, action hierarchy, autocomplete overlay behavior, date inheritance behavior, UOM display contract, and shell lifecycle discipline.
- Reports are protected by the Phase 4A report shell and final protected gate. Purchase Order Analysis, Demand-to-Order Coverage, Item Purchase History, and Reports Index have screenshot evidence in the final protected gate.
- Supplier Detail, Item Detail, and PO Follow-up Detail have screenshot evidence and are protected read/detail surfaces.
- Worklist filter responsiveness is protected for key directory surfaces through final protected gate artifacts.
- Productized create actions for Purchase Request, RFQ, Supplier Quotation, and Purchase Order are protected by focused managed-form smoke coverage.

### Page-Specific Weaknesses And Audit Items

| Page or family | Finding | Severity | Recommended treatment |
| --- | --- | --- | --- |
| Procurement Overview | Likely functionally correct and protected, but post-Phase-5 full visual screenshot evidence is not explicit in final artifact scan. | Medium evidence gap | Capture 1136/1440 screenshots before redesign. Then evaluate card density, Start Buying Work hierarchy, and supplier-facing next steps. |
| Sidebar/navigation | Protected by smoke, but should be checked against final form family for active-state clarity and route grouping. | Low | Include in Phase 6D visual capture. |
| Search | Source exists and is role-scoped, but visual/empty/error states are not evidenced in Phase 6A. | Medium | Add search smoke/screenshots; verify no native route leakage from results. |
| Supplier Directory | Narrow filter evidence exists; full desktop visual state needs capture. | Medium | Phase 6D audit should verify table density, action placement, and native Supplier Form exception styling. |
| Purchase Request Directory | Protected create action, but full page visual evidence should be refreshed after managed form completion. | Low/medium | Capture and compare to PR form visual language. |
| Requests to Source | Business-sensitive because PR-to-RFQ remains deferred. Needs clear unavailable/deferred state if users expect conversion. | Medium | Phase 6D or 6E design should clarify submitted/request state and conversion prerequisites. |
| RFQ Directory | Managed New RFQ route protected; future send/output workflow will change this page. | High for future 6B | Do not add send actions ad hoc. Design output states first. |
| Supplier Quotation Directory | Managed New Supplier Quotation protected; quote comparison action should remain clear. | Medium | Capture full desktop and ensure Compare path is visible but not award/create-PO. |
| Purchase Order Directory | Managed New Purchase Order protected; future output/send and lifecycle actions are tempting but forbidden until designed. | High for future 6B/6F | Preserve draft-entry scope; design supplier-facing output separately. |
| Reports Index | Protected screenshot exists; may need higher-order grouping once document output and conversion phases exist. | Low | Redesign only after 6B/6C decisions. |
| Quote Comparison | Business-critical; current wrapper supports comparison but does not award/create PO. | High | Keep read/decision support; future award path must be separate governed conversion phase. |
| Purchase Order Analysis | Protected; should remain read/reporting, not operational lifecycle execution. | Medium | Add stronger drilldown screenshot coverage before 6D. |
| Demand-to-Order Coverage | Protected; central to future conversion planning. | Medium | Use as evidence for PR/RFQ/PO conversion design later. |
| Item Purchase History | Protected; must not mutate Item Price. | Medium | Future analytics can suggest, but mutations remain deferred. |
| Supplier Detail | Screenshot exists; likely older compact detail style than forms. | Medium | Phase 6D can polish hierarchy without adding master-data edit scope. |
| Item Detail | Screenshot exists; must keep Item Price/default supplier changes forbidden. | Medium | Phase 6D can improve read-only buying posture, not mutate master data. |
| Purchase Request Review | Protected read/review page; conversion expectations need clearer business state later. | Medium | Future 6E conversion design only after submit/review governance. |
| RFQ Review | Needs supplier-facing output workflow integration in future. | High for 6B | Design Print/PDF/Email/Send and status/audit before implementation. |
| Supplier Quotation Review | Compare offers action is accepted; no create PO. | Medium/high | Future SQ-to-PO conversion must be governed and likely after submitted/validated offer state. |
| PO Follow-up Detail | Screenshot exists; read/follow-up only. | High for 6B/6F | Future output and lifecycle actions need separate design/ownership. |
| Managed PR/RFQ/SQ/PO forms | Protected baseline. | Protected | Do not alter without focused form smoke and protected gate. |

### Cross-Cutting UI Findings

- The form family is now the quality benchmark for future Procurement work.
- Older worklist/detail/report surfaces should be visually evaluated against the managed form standard before broad polish.
- Existing evidence proves protection, not necessarily final premium visual acceptance for every non-form page.
- Native exception buttons must keep secondary styling and never become primary workflow actions.
- Page stacking, duplicate shell, autocomplete clipping, and column-label collision defects have occurred in Phase 5 and should remain explicit smoke checks.
- The route/governance manifest appears to contain legacy native create exception classifications and older labels for some Phase 5 managed actions, including RFQ create and Purchase Request save wording. Runtime and smokes are protected, but Phase 6 should reconcile governance metadata so future agents do not misread the source of truth.

## Business Workflow Evaluation

Current business model is coherent:

- Purchase Request: internal purchase demand capture. It is not supplier communication and not a purchase commitment.
- RFQ: supplier sourcing request draft. It may become supplier-facing, but Phase 5B did not send or print it.
- Supplier Quotation: supplier offer record for buyer comparison or later award decision. It can be directly entered without RFQ in the current protected baseline.
- Purchase Order: supplier order draft. It can become a commitment only after separate ERPNext submit/approval and downstream governance.
- Quote Comparison: sourcing decision support. It must remain read/compare until a governed award path exists.
- PO Follow-up: buyer tracking and visibility, not receiving/billing/payment execution.
- Reports: decision review and drilldown surfaces, not mutation surfaces.

### Supplier-Facing Document Output Need

RFQs and Purchase Orders are supplier-facing documents. The current managed forms can record RFQ and PO drafts, but the workspace does not yet provide a governed output path.

Future RFQ/PO output must include design for:

- Print layout.
- PDF generation.
- Email/send to supplier.
- Supplier recipient selection from supplier contacts.
- CC/BCC and buyer sender identity policy.
- Email template and subject/body defaults.
- Branded document layout with company identity and address details.
- Draft watermark/status labeling so unsent/unsubmitted drafts are not confused with final commitments.
- Terms and conditions.
- Attachments.
- Communication/audit log.
- Permission boundaries for who can preview, print, generate PDF, and send.
- Native ERPNext print/email compatibility versus fully managed output.
- Error/retry states for email failures.
- Whether sending requires document submit, review, or manager approval.

Recommendation: RFQ/PO output should be the near-term next designed phase because it is required for a complete buyer workflow, but it must be design-first. Do not add Print/PDF/Email/Send buttons directly to forms or review pages without Phase 6B approval.

## Native Leakage And Safety Evaluation

| Native access or mutation | Classification | Phase 6A decision |
| --- | --- | --- |
| Saved-form `Open ERP Form` | Accepted governed exception | Preserve as secondary only after save |
| Review/detail `Open ERP Form` | Accepted governed exception | Preserve as secondary only |
| ERP Supplier Form | Accepted governed exception | Secondary only, permission-gated |
| ERP Item Form | Accepted governed exception | Secondary only, no Item Price/default supplier mutation from productized pages |
| Raw native create forms for PR/RFQ/SQ/PO | Deferred cleanup/governance compatibility | Productized primary create must stay managed; update manifest/docs later to avoid confusion |
| Native `Get Items From` | Governed native lifecycle tool | Allowed only in native ERP form context; future managed source flows must use ERPNext mapping APIs |
| Submit/Approve/Reject | Forbidden in current managed Procurement surface | Future 6F or separate approval phase only |
| Create PO from Supplier Quotation | Forbidden for now | Future conversion phase only after native mapping and document-state governance |
| Receive/Create Purchase Receipt | Forbidden | Warehouse-owned or joint phase later |
| Bill/Create Purchase Invoice | Forbidden | Finance-owned or joint phase later |
| Payment/Pay | Forbidden | Finance/payment phase later |
| Item Price mutation | Forbidden | Separate pricing governance only |
| Default Supplier mutation | Forbidden | Separate master-data governance only |
| Supplier/Item master-data mutation | Forbidden | Separate master-data phase only |

No mutation action is proposed as default Phase 6 implementation.

## Protected Baseline Impact Review

Future phases must protect:

- Frozen Sales Console.
- Phase 5A Managed Purchase Request.
- Phase 5B Managed RFQ.
- Phase 5C Managed Supplier Quotation.
- Phase 5D Managed Purchase Order.
- Phase 4A reports/worklists/detail baselines.
- Native exception policy.

Required validation gates for future work:

- `python3 -m compileall erp_workspace_ui`.
- `PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'`.
- `node --check` for touched JS/smoke files.
- `git diff --check HEAD`.
- Focused smoke for every affected managed form or surface.
- Full protected workspace gate after runtime changes.
- Sales freeze protection for any shared runtime/CSS/component or registry change.

Recommended gate improvements:

- Add an explicit Phase 6 screenshot capture matrix for all Procurement routes at 1136x768 and 1440x900.
- Add a Procurement search smoke covering ready, empty, restricted, and result-click states.
- Add native leakage assertions for RFQ/PO output once designed.
- Add supplier-facing output smokes for preview, PDF generation, email-send disabled/ready states, recipient validation, and audit-log evidence once implemented.
- Add a manual visual checklist artifact for major protected baselines, not only automation summaries.
- Reconcile governance manifest labels and route classifications with Phase 5A-5D managed-form reality.
- Consider performance thresholds for Overview, large worklists, report load, and managed forms.

## Prioritized Future Phase Roadmap

### Phase 6B: Supplier-Facing Document Output Design

Problem:

RFQ and Purchase Order are supplier-facing documents, but the workspace has no governed output design.

Scope:

- RFQ print/PDF/email/send design.
- PO print/PDF/email/send design.
- Template/branding requirements.
- Supplier contact/recipient selection.
- Email subject/body defaults and override policy.
- Attachment support.
- Draft/final status labeling and watermark policy.
- Terms and conditions handling.
- Audit trail/communication log requirements.
- Permission model for preview, print, PDF, send.
- Native ERPNext print/email wrapper versus managed output decision.

Exclusions:

- No implementation.
- No submit/approval/receive/bill/payment.
- No conversions.
- No AI intake.

Validation/protection:

- Design doc only.
- Cite ERPNext native print/email capabilities from installed source where relevant.
- Define smoke plan before implementation.

### Phase 6C: Supplier-Facing Document Output Implementation

Problem:

Approved RFQ/PO output design must become a safe productized workflow.

Scope:

- Implement only the owner-approved Phase 6B output contract.
- RFQ preview/PDF/email/send if approved.
- PO preview/PDF/email/send if approved.
- Communication/audit state if approved.
- Permission-aware backend APIs.

Exclusions:

- No conversions unless separately approved.
- No lifecycle submit/approval/receive/bill/payment.
- No Item Price or Default Supplier mutation.

Validation/protection:

- Python contract tests.
- Email/PDF/print smoke with non-destructive test mode or controlled recipient policy.
- Focused RFQ and PO smokes.
- Sales freeze if shared runtime touched.
- Full protected workspace gate.
- Manual document visual review for PDF/print output.

### Phase 6D: Procurement Workspace UI Polish/Redesign

Problem:

Non-form Procurement pages likely trail the managed form family in visual polish and evidence coverage.

Scope:

- Capture all pages first.
- Improve Overview, directories, reports, detail/review pages, search, and native exception styling using page-specific findings.
- Align action hierarchy, spacing, table readability, filters, empty states, and responsive behavior with accepted Sales/Procurement standards.

Exclusions:

- No new business mutations.
- No conversions.
- No output/send unless completed in 6C.
- No broad shared component change without Sales freeze.

Validation/protection:

- Page-by-page screenshots at 1136x768 and 1440x900.
- Worklist/detail/report smokes.
- Focused managed form regression smokes for PR/RFQ/SQ/PO.
- Full protected workspace gate.

### Phase 6E Or Later: Conversion Workflows

Problem:

Procurement needs traceable source-document conversions, but ERPNext native mapping generally depends on submitted/governed upstream documents.

Scope candidates:

- PR-to-RFQ.
- RFQ-to-Supplier Quotation.
- Supplier Quotation-to-Purchase Order.
- PR/MR-to-Purchase Order.

Exclusions:

- No custom row-copy bypass of ERPNext mapping/business validation.
- No conversion from draft-only internal records unless owner approves a governed review/submit step.

Validation/protection:

- Native method verification from installed ERPNext source.
- State eligibility tests.
- Source reference preservation tests.
- Permission and role tests.
- Focused conversion smoke.
- Full protected workspace gate.

### Phase 6F Or Later: Operational Lifecycle

Problem:

Submit/approval/receiving/billing/payment cross workspace boundaries and create financial/stock effects.

Scope candidates:

- PO submit/approval/rejection.
- Purchase Receipt/receiving workflow.
- Purchase Invoice/billing workflow.
- Payment status handoff.
- Warehouse and Finance ownership boundaries.

Exclusions:

- No ad-hoc lifecycle buttons inside current managed forms.
- No finance/warehouse mutation without explicit owner design.

Validation/protection:

- Cross-role tests for Purchase, Warehouse, Finance, and Executive approver roles.
- ERPNext workflow state tests.
- Audit trail tests.
- Full protected workspace gate and any Warehouse/Finance gates once those consoles exist.

### Future Strategic Work

- AI supplier quotation intake with document upload/OCR/extraction and human review.
- Supplier portal or supplier response workflow.
- Supplier scorecard.
- Advanced procurement analytics.
- Master-data governance for Supplier/Item maintenance, Item Price, and Default Supplier.

## Immediate Next Recommendation

Start Phase 6B as a design-only supplier-facing document output phase. It should decide how RFQ and Purchase Order print/PDF/email/send work before any button appears in the UI.

Do not begin broad UI redesign first. The missing supplier-facing output path is a clearer business gap, and its decisions will affect RFQ Review, PO Follow-up, managed RFQ/PO saved states, permissions, audit logging, and future visual redesign.

Before Phase 6D implementation, run or create a no-code full Procurement screenshot audit so that non-form pages are judged from current evidence rather than assumptions.

## Explicit Deferrals

The following remain deferred and are not implemented by Phase 6A:

- RFQ print/PDF/email/send implementation.
- PO print/PDF/email/send implementation.
- PR-to-RFQ conversion.
- RFQ-to-Supplier Quotation conversion.
- Supplier Quotation-to-Purchase Order conversion.
- Material Request/Purchase Request-to-Purchase Order conversion.
- Submit/approval/rejection workflow.
- Receiving and Purchase Receipt creation.
- Billing and Purchase Invoice creation.
- Payment workflow.
- AI supplier quotation intake.
- Supplier portal.
- Supplier scorecard.
- Item Price mutation.
- Default Supplier mutation.
- Supplier or Item master-data create/edit.
- Broad Procurement redesign implementation.

## Documentation Validation Scope

This Phase 6A task is docs-only. Runtime source, smoke scripts, Sales Console, shared components, and live deployment must remain untouched.
