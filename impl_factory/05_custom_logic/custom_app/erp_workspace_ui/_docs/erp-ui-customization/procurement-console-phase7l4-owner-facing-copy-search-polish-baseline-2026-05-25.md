# Procurement Console Phase 7L4 Owner-Facing Copy and Search Polish Baseline

Date: 2026-05-25
Branch: `feature/erpnext-ui-design`
Accepted implementation commit: `db0c569e61f942ab59da6a4c064747633dd8547a`
Baseline type: protected docs-only closure after accepted runtime implementation, live alignment, Main Agent verification, and owner manual acceptance

## 1. Status

Phase 7L4 is closed as a protected baseline for Procurement owner-facing copy cleanup and conservative shared Search input polish.

Owner manual review and Main Agent V3 verification accepted the runtime implementation at commit `db0c569e61f942ab59da6a4c064747633dd8547a`. This document records the accepted behavior, evidence, and protection contract. It does not introduce runtime, smoke, test, data, or live changes.

## 2. Phase Scope

Phase 7L4 removed developer/governance-facing wording from visible Procurement runtime UI and polished the shared Search modal input presentation.

Accepted cleanup areas included:

- Procurement Overview Quick Find subtitle, placeholder, empty state, suggestion fallback, and preview note copy.
- Procurement Quick Find supplier, item, request, RFQ, supplier quotation, purchase order, and report previews.
- RFQ supplier communication and output copy.
- PO output and follow-up copy.
- Manager readiness helper copy.
- Managed PR/RFQ/SQ/PO unsupported-field validation copy.
- Procurement report catalog and report boundary copy.
- Shared Search modal visual input polish used by Procurement Console and Sales Console.

The phase intentionally did not change search semantics, result groups, routing, Quick Find Open behavior, Search keyboard behavior, or Sales business behavior.

## 3. Accepted Copy Contract

Visible Procurement runtime copy must remain business-facing. Normal users must not see implementation or governance vocabulary such as:

- `Productized`
- `native ERP`
- `native form`
- `route only`
- `No native`
- `governed`
- `deferred`
- `future governed`
- `forbidden`
- `mutation`

Accepted business-facing replacements include:

- `Open the Procurement page for this record.`
- `Open this Procurement report.`
- `Email sending is not active yet. Preview and PDF remain available.`
- `Guidance only. Review before the next buying step.`
- `This form can only update approved fields. Remove unsupported fields and try again.`

Internal comments, internal function names, and non-visible governance symbols may retain implementation terms when needed for code clarity and policy enforcement.

## 4. Accepted Search and Quick Find Presentation

Quick Find accepted behavior and presentation:

- Quick Find remains below `Start Buying Work` and above `Readiness Review`.
- The subtitle reads: `Find a procurement record, preview it, then open its Procurement page.`
- The input placeholder is lighter and less dominant than before.
- Search status copy remains business-facing.
- Selecting a suggestion renders a preview first.
- Navigation still requires the explicit `Open` button.
- Enter still does not auto-open a result.
- Preview notes no longer mention productized routes, native ERP forms, or developer-only boundaries.

Shared Search accepted behavior and presentation:

- Procurement Ctrl+K/Search and Sales Ctrl+K/Search keep their existing modal pattern.
- The modal input is visually lighter and better balanced below the modal title.
- Result grouping, badges, keyboard behavior, and routing remain unchanged.
- Sales Search visual polish was accepted as a shared-shell styling change, with no Sales behavior change.

## 5. Validation Evidence

Accepted final evidence:

- Runtime copy scan: `/tmp/procurement-phase7l4-copy-scan-source-20260525T122100Z/runtime-copy-scan.json`
- Focused source Quick Find/Search: `/tmp/procurement-phase7l4-quickfind-source-final-rerun-20260525T122706Z/procurement-phase7l4-quickfind-source-final-rerun/phase7k-summary.json`
- Focused source shared Search: `/tmp/procurement-phase7l4-workspace-search-source-rerun2-20260525T121410Z/workspace-search-20260525T121633Z/workspace-search-summary.json`
- Source Sales freeze: `/tmp/procurement-phase7l4-sales-freeze-source-rerun-20260525T130705Z/sales-freeze-protection-summary.json`
- Source protected workspace gate: `/tmp/procurement-phase7l4-protected-source-20260525T131205Z/protected-workspace-gate-summary.json`
- Live Quick Find/Search: `/tmp/procurement-phase7l4-quickfind-live-20260525T135532Z/procurement-phase7l4-quickfind-live/phase7k-summary.json`
- Live shared Procurement/Sales Search: `/tmp/procurement-phase7l4-workspace-search-live-20260525T135700Z/workspace-search-20260525T141610Z/workspace-search-summary.json`
- Live Phase 7L performance: `/tmp/procurement-phase7l4-performance-live-20260525T141720Z/procurement-phase7l4-performance-live/phase7l-performance-summary.json`
- Final protected workspace gate: `/tmp/procurement-phase7l4-protected-live-20260525T141825Z/protected-workspace-gate-summary.json`
- Sales freeze inside final protected gate: `/tmp/procurement-phase7l4-protected-live-20260525T141825Z/sales-freeze-protection/sales-freeze-protection-summary.json`

Final protected gate status:

- Overall status: pass.
- Head commit: `db0c569e61f942ab59da6a4c064747633dd8547a`.
- Changed files at final gate: none.
- Remaining untracked file: `ui_smoke/sales_final_acceptance_audit.js`.
- Sales freeze inside protected gate: pass.

Runtime copy scan status:

- Status: pass.
- Remaining visible or review hits: none.
- Remaining risky terms are classified as internal comments, internal symbols, payload flags, guard variables, or copy-sanitizing scan logic.

## 6. Screenshot Evidence

Accepted live screenshot evidence includes:

- Procurement Quick Find empty state: `/tmp/procurement-phase7l4-quickfind-live-20260525T135532Z/procurement-phase7l4-quickfind-live/manager-laptop-1136-quick-find-empty.png`
- Procurement Quick Find supplier preview: `/tmp/procurement-phase7l4-quickfind-live-20260525T135532Z/procurement-phase7l4-quickfind-live/manager-laptop-1136-supplier-preview.png`
- Procurement Quick Find purchase request preview: `/tmp/procurement-phase7l4-quickfind-live-20260525T135532Z/procurement-phase7l4-quickfind-live/manager-request-preview.png`
- Procurement Quick Find report preview: `/tmp/procurement-phase7l4-quickfind-live-20260525T135532Z/procurement-phase7l4-quickfind-live/manager-report-preview.png`
- Procurement Search modal: `/tmp/procurement-phase7l4-workspace-search-live-20260525T135700Z/workspace-search-20260525T141610Z/procurement-search-button-pur.png`
- Sales Search modal: `/tmp/procurement-phase7l4-workspace-search-live-20260525T135700Z/workspace-search-20260525T141610Z/sales-search-button-35.png`

Main Agent V3 screenshot verification accepted the visuals.

## 7. Source / Live Hash Proof

All synced runtime source/live hashes matched. Full hash evidence is recorded at:

- `/tmp/procurement-phase7l4-live-alignment-20260525T133115Z/source-live-hashes.json`

Key accepted hashes include:

| File | SHA-256 |
| --- | --- |
| `erp_workspace_ui/procurement_console/service.py` | `88a6aa4a0cfc09bd7b0f408d85501bddd84ea50b4d44ca188e292f6677350d23` |
| `erp_workspace_ui/procurement_console/document_output.py` | `da57699a3ce7fd298c848ba9fc410de6d1f5a28a2b216d9074abedcf76187378` |
| `erp_workspace_ui/procurement_console/readiness.py` | `139300f913c6c96a5cc337c31047b9212a2e31a8d5f0127364d8d42a8ccf5870` |
| `erp_workspace_ui/public/css/erp_workspace_ui.css` | `986c916ba46beb7e7dabc502eeaa49f3cc641a924b3bd41102df1fe2d3e20328` |
| `erp_workspace_ui/public/js/procurement_console/procurement_console_page.js` | `9d229c0aa31be067803041ab228620516493d659889f9cafc65ca720b73bed22` |
| `erp_workspace_ui/public/js/runtime/console/workspace_console_sidebar.js` | `23011e56c70e7309929e79c16f3c0804b79c397ef36325a589948884e46f8ec5` |

No docs-only closure live alignment is required.

## 8. Manual Acceptance

Owner manual check passed after live alignment.

Manual review confirmed:

- Procurement Quick Find preview no longer shows developer/governance wording.
- Quick Find supplier, request, and report previews use business-facing copy.
- Quick Find placeholder is lighter and less dominant.
- Procurement Search modal input is visually balanced and grouped results still work.
- Sales Search modal remains usable and grouped results still work.
- RFQ/PO output and readiness copy communicates that sending/email is not active without exposing implementation terms.

Main Agent verification also confirmed that Sales Search styling changed as a shared-shell polish, but Sales Search behavior did not change and Sales freeze passed.

## 9. Protected Behavior Contract

Future changes must preserve:

- Owner-facing Procurement UI must not expose developer/governance terms listed in Section 3.
- Quick Find still requires explicit Open.
- Quick Find Enter key must not auto-open.
- Quick Find result groups and route targets remain unchanged unless an owner-approved phase changes them.
- Shared Search keeps existing grouping, routing, Ctrl+K behavior, and keyboard navigation.
- Sales Search behavior remains protected when shared Search styling changes.
- Procurement native ERP escape remains closed for normal Purchase Manager and Purchase User paths.
- Runtime copy scans must be run before future freeze closure if visible text changes.

## 10. Forbidden / Deferred Scope

Phase 7L4 did not introduce or start:

- Sales Search behavior changes.
- Sales backend or API changes.
- Native ERP form or report escape.
- RFQ or PO send.
- Email or SMTP runtime.
- Communication or Email Queue creation.
- Contact, User, or portal creation.
- Submit, approval, rejection, cancel, amend, or conversion lifecycle actions.
- Receiving, billing, or payment mutation.
- Item Price mutation.
- Default Supplier mutation.
- Item Supplier mutation.
- AI intake.

## 11. Manual Check Instructions

As Purchase Manager:

1. Open Procurement Overview at 1136px.
2. Confirm Quick Find subtitle and placeholder are business-facing and visually lighter.
3. Search a supplier, select it, and confirm the preview says `Open the Procurement page for this record.` or similarly business-facing copy.
4. Search a purchase request and report, then confirm the previews do not show productized/native/governed/deferred wording.
5. Open Procurement Search with Ctrl+K or the Search sidebar action and confirm the modal remains visually balanced.
6. Confirm grouped results still work.

As Purchase User:

1. Repeat Quick Find and Search checks on visible records.
2. Confirm no manager-only or native ERP action appears.

As Sales Manager/User:

1. Open Sales Search with Ctrl+K or the Search sidebar action.
2. Confirm grouped results still work.
3. Confirm no Search routing, keyboard, or behavior regression appears.

## 12. Recommended Next Task

Phase 7L4 is now closed as a protected baseline.

Recommended next step is a final owner-facing Procurement freeze closure package after owner/Main Agent acceptance of the full Procurement workspace. The closure should remain docs-only unless a new freeze-blocking issue is found.
