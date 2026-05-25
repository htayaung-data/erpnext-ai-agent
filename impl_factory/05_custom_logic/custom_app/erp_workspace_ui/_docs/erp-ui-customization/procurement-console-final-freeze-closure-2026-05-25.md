# Procurement Console Final Freeze Closure

Date: 2026-05-25
Branch: `feature/erpnext-ui-design`
Final accepted runtime commit: `db0c569e61f942ab59da6a4c064747633dd8547a`
Final baseline closure commit: pending at document creation
Freeze type: protected docs-only final closure package

## 1. Status

Procurement Console is accepted for protected freeze after owner manual review, Main Agent verification, live alignment, and final protected workspace gates.

This document consolidates the accepted Procurement Console state after Phase 7L4. It does not introduce runtime, smoke, test, data, or live changes.

The Procurement Console should now be treated as a protected workspace baseline in the same operating discipline as Sales Console: future changes must be explicitly phased, scoped, validated, and protected against regression.

## 2. Final Accepted Scope

The frozen Procurement Console includes these accepted surfaces and behaviors:

- Procurement Overview with KPIs, `Start Buying Work`, Quick Find, and Readiness Review.
- Productized Procurement navigation shell for Purchase Manager and Purchase User.
- Supplier Directory and Supplier Detail.
- Buying Item Directory and Buying Item Detail.
- Purchase Request Directory, Review page, and managed new/saved form.
- RFQ Directory, Review page, managed new/saved form, Supplier Communication readiness, Preview RFQ, and Download RFQ PDF.
- Supplier Quotation Directory, Review page, and managed new/saved form.
- Purchase Order Directory, Follow-up Detail, managed new/saved form, Preview Purchase Order, and Download PO PDF.
- Productized Procurement report catalog and report pages.
- Quote Comparison, Purchase Order Analysis, Demand-to-Order Coverage, and Item Purchase History report pages.
- Supplier Buying Profile and Contact Readiness companion context.
- Item Buying Context companion context.
- Manager Readiness Review queue with async performance behavior.
- Overview Quick Find with grouped suggestions, compact preview, and explicit Open.
- Shared Search modal visual polish accepted for Procurement and Sales, with Sales behavior preserved.

## 3. Final Information Architecture

Accepted Overview order:

1. Procurement header and KPI cards.
2. `Start Buying Work` action cards.
3. `Quick Find`.
4. `Readiness Review`.

Accepted Supplier Detail tabs:

- `Profile`
- `Orders`
- `RFQs`
- `Quotations`

Accepted Buying Item Detail tabs:

- `Profile`
- `Suppliers & Prices`
- `Orders`
- `Quotation History`

Supplier and Buying Item detail pages are object-profile pages, not long vertical stacks. The Profile tab is the default. Long history lists are bounded and must not grow into uncontrolled full-history vertical stacks inside the object page.

## 4. Final Behavior Contracts

Protected behavior:

- Normal Purchase Manager and Purchase User paths must stay inside productized Procurement routes.
- Native ERP form/report escape links must remain absent for normal Procurement users.
- Quick Find selection must show preview before navigation.
- Quick Find Open must remain explicit.
- Enter in Quick Find must not auto-open a result.
- Directory and worklist filters remain Apply-based and must not become auto-navigation search.
- Supplier and Item readiness/profile edits remain companion-context updates only.
- Broad Supplier master data and Item master data remain protected from direct normal-role mutation.
- Item Price, Default Supplier, and Item Supplier mutation remain forbidden.
- RFQ and PO supplier-facing output remains Preview/PDF only.
- RFQ/PO send/email remains inactive.
- Receiving, billing, and payment remain outside Procurement Console.
- Sales Console remains frozen and protected when shared runtime changes are made.

## 5. Final Copy Contract

Visible Procurement runtime copy must be business-facing.

Normal users must not see implementation or governance vocabulary such as:

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

Accepted language includes:

- `Open the Procurement page for this record.`
- `Open this Procurement report.`
- `Email sending is not active yet. Preview and PDF remain available.`
- `Guidance only. Review before the next buying step.`
- `This form can only update approved fields. Remove unsupported fields and try again.`

Future visible-copy changes must run a runtime copy scan before closure.

## 6. Final Performance Contract

Accepted final performance posture:

- Procurement warm route lifecycle duplication was fixed in Phase 7L1.
- Manager Readiness is asynchronous and must not block primary Overview content.
- Manager Readiness direct API performance is guarded by median, p95, and max thresholds rather than a brittle max-only threshold.
- Purchase User Overview must not call Manager Readiness.
- Quick Find API performance remains guarded.
- Frappe Desk cold first-load platform cost is not classified as a Procurement route lifecycle defect, but custom Procurement warm-route regressions remain unacceptable.

Accepted Phase 7L4 live performance evidence:

- Live Phase 7L performance: `/tmp/procurement-phase7l4-performance-live-20260525T141720Z/procurement-phase7l4-performance-live/phase7l-performance-summary.json`
- Manager Readiness median: `297 ms`, p95: `356 ms`, max: `356 ms`.
- Quick Find median: `88 ms`, p95: `103 ms`, max: `103 ms`.
- Performance failures: none.

## 7. Final Validation Evidence

Final accepted runtime implementation and gate evidence:

- Final runtime copy/search polish commit: `db0c569e61f942ab59da6a4c064747633dd8547a`.
- Runtime copy scan: `/tmp/procurement-phase7l4-copy-scan-source-20260525T122100Z/runtime-copy-scan.json`.
- Live Quick Find/Search: `/tmp/procurement-phase7l4-quickfind-live-20260525T135532Z/procurement-phase7l4-quickfind-live/phase7k-summary.json`.
- Live shared Procurement/Sales Search: `/tmp/procurement-phase7l4-workspace-search-live-20260525T135700Z/workspace-search-20260525T141610Z/workspace-search-summary.json`.
- Final protected workspace gate: `/tmp/procurement-phase7l4-protected-live-20260525T141825Z/protected-workspace-gate-summary.json`.
- Sales freeze inside final protected gate: `/tmp/procurement-phase7l4-protected-live-20260525T141825Z/sales-freeze-protection/sales-freeze-protection-summary.json`.

Final protected gate facts:

- Overall status: pass.
- Head commit: `db0c569e61f942ab59da6a4c064747633dd8547a`.
- Changed files at gate: none.
- Remaining untracked file: `ui_smoke/sales_final_acceptance_audit.js`.
- Sales freeze: pass.

## 8. Final Screenshot Evidence

Accepted owner-facing screenshot evidence includes:

- Procurement Quick Find empty state: `/tmp/procurement-phase7l4-quickfind-live-20260525T135532Z/procurement-phase7l4-quickfind-live/manager-laptop-1136-quick-find-empty.png`
- Procurement Quick Find supplier preview: `/tmp/procurement-phase7l4-quickfind-live-20260525T135532Z/procurement-phase7l4-quickfind-live/manager-laptop-1136-supplier-preview.png`
- Procurement Quick Find purchase request preview: `/tmp/procurement-phase7l4-quickfind-live-20260525T135532Z/procurement-phase7l4-quickfind-live/manager-request-preview.png`
- Procurement Quick Find report preview: `/tmp/procurement-phase7l4-quickfind-live-20260525T135532Z/procurement-phase7l4-quickfind-live/manager-report-preview.png`
- Procurement Search modal: `/tmp/procurement-phase7l4-workspace-search-live-20260525T135700Z/workspace-search-20260525T141610Z/procurement-search-button-pur.png`
- Sales Search modal: `/tmp/procurement-phase7l4-workspace-search-live-20260525T135700Z/workspace-search-20260525T141610Z/sales-search-button-35.png`

Owner manual review accepted the final UI.

## 9. Final Source / Live Hash Evidence

The full Phase 7L4 live alignment hash proof is recorded at:

- `/tmp/procurement-phase7l4-live-alignment-20260525T133115Z/source-live-hashes.json`

All 21 synced runtime source/live hashes matched.

Key final hashes:

| File | SHA-256 |
| --- | --- |
| `erp_workspace_ui/procurement_console/service.py` | `88a6aa4a0cfc09bd7b0f408d85501bddd84ea50b4d44ca188e292f6677350d23` |
| `erp_workspace_ui/procurement_console/document_output.py` | `da57699a3ce7fd298c848ba9fc410de6d1f5a28a2b216d9074abedcf76187378` |
| `erp_workspace_ui/procurement_console/readiness.py` | `139300f913c6c96a5cc337c31047b9212a2e31a8d5f0127364d8d42a8ccf5870` |
| `erp_workspace_ui/public/css/erp_workspace_ui.css` | `986c916ba46beb7e7dabc502eeaa49f3cc641a924b3bd41102df1fe2d3e20328` |
| `erp_workspace_ui/public/js/procurement_console/procurement_console_page.js` | `9d229c0aa31be067803041ab228620516493d659889f9cafc65ca720b73bed22` |
| `erp_workspace_ui/public/js/runtime/console/workspace_console_sidebar.js` | `23011e56c70e7309929e79c16f3c0804b79c397ef36325a589948884e46f8ec5` |

This docs-only final closure does not require live alignment.

## 10. Frozen Baseline Documents

This final closure depends on the accepted Procurement baselines and design records, especially:

- `procurement-console-phase3-stable-baseline-2026-05-10.md`
- `procurement-console-phase5a-5b-managed-buying-baseline-2026-05-15.md`
- `procurement-console-phase5c-managed-supplier-quotation-baseline-2026-05-15.md`
- `procurement-console-phase5d-managed-purchase-order-baseline-2026-05-15.md`
- `procurement-console-phase6c1-output-preview-pdf-baseline-2026-05-16.md`
- `procurement-console-phase6c2a-rfq-send-readiness-baseline-2026-05-16.md`
- `procurement-console-phase7d1-native-escape-closure-baseline-2026-05-18.md`
- `procurement-console-phase7h1-readiness-inference-exception-queue-baseline-2026-05-20.md`
- `procurement-console-phase7i-full-freeze-audit-baseline-2026-05-20.md`
- `procurement-console-phase7j1d-readiness-review-polish-baseline-2026-05-23.md`
- `procurement-console-phase7j2c-supplier-item-tab-simplification-baseline-2026-05-24.md`
- `procurement-console-phase7k-overview-quick-find-baseline-2026-05-24.md`
- `procurement-console-phase7l4-owner-facing-copy-search-polish-baseline-2026-05-25.md`

## 11. Future Change Gate

Any future Procurement Console change must start with a named phase and must include:

1. Source gate and dirty-file classification.
2. Explicit scope and non-goals.
3. Protection of Sales Console and shared runtime surfaces.
4. Static scans for native escape, send/email, lifecycle, and copy risk when relevant.
5. Focused smoke for touched surfaces.
6. Sales freeze if shared runtime, navigation, search, list shell, report shell, or CSS is touched.
7. Full protected workspace gate before final acceptance.
8. Source/live hash verification after live alignment.
9. Owner manual check for owner-facing UI changes.
10. Docs-only baseline closure after acceptance.

## 12. Explicit Deferrals

The final Procurement freeze does not implement or authorize:

- RFQ send/email activation.
- PO send/email activation.
- SMTP or email infrastructure setup.
- Communication or Email Queue creation.
- Contact, User, or supplier portal creation.
- Submit, approval, rejection, cancel, amend, or conversion lifecycle actions.
- PR-to-RFQ, RFQ-to-SQ, SQ-to-PO, or PR-to-PO conversion execution.
- Receiving, stock movement, warehouse operations, billing, payment, or finance posting.
- Item Price mutation.
- Default Supplier mutation.
- Item Supplier mutation.
- Supplier broad master-data administration.
- Item broad master-data administration.
- AI quotation intake.
- Native ERPNext route escape for normal Procurement users.

These remain future phases and must be designed before implementation.

## 13. Recommended Next Workspace

With Procurement Console frozen, the recommended next workspace is Warehouse Console.

Reason:

- Procurement intentionally stops before receiving and stock movement.
- Purchase Orders now provide buyer follow-up and read-only status posture.
- Warehouse should own receiving, stock movement visibility, warehouse queues, and inventory operations.
- Warehouse work can build on the same protected workspace contracts while keeping Procurement frozen.

The next workspace should start from:

- `frozen-workspace-protection-package-standard-v1.md`
- `shared-core-workspace-adapter-contract-v2.md`
- `native-exception-policy-v1.md`
- `workspace_governance_manifest.py`
- `shared-component-and-implementation-golden-rule-standard-v1.md`
- the accepted Sales and Procurement final freeze baselines
