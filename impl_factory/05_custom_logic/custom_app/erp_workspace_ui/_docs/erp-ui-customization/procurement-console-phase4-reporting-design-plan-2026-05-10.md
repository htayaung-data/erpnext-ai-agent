# Procurement Console Phase 4 Reporting Design Plan

Date: 2026-05-10

Status: design proposal only. No runtime implementation is approved by this document.

Source branch: `feature/erpnext-ui-design`

Source repo: `/home/deploy/erp-projects/erpai_project1_erpnext_ui_design`

Custom app: `/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/05_custom_logic/custom_app/erp_workspace_ui`

Latest baseline reviewed: `Procurement Console Phase 3 Stable Baseline`, accepted on 2026-05-10.

## 1. Design Rule

Phase 4 is a reporting, analytics, and buyer decision review phase. It must preserve the accepted Phase 3 workbench and must not start Managed Procurement Forms.

Phase 4 must not implement:

- Managed Purchase Request, RFQ, Supplier Quotation, or Purchase Order forms.
- Supplier create/edit.
- Item create/edit.
- Purchase approval/rejection shortcuts.
- Submit, cancel, amend, close, receive, bill, pay, or workflow mutation actions.
- Warehouse receiving execution.
- Purchase Invoice, payment, payable settlement, or accounting execution.
- Item Price mutation.
- Default Supplier mutation.
- Supplier portal or supplier email-sending workflow.
- Supplier scorecard unless data, permissions, and ownership are separately approved.

## 2. Phase 3 Baseline Read

Accepted Phase 3 includes:

- Procurement Overview.
- Supplier Directory and read-only Supplier Detail.
- Buying Item Directory and read-only Buying Item Detail.
- Purchase Request Directory, Requests To Source, and Purchase Request Review.
- RFQ Directory, RFQs Awaiting Supplier Response, RFQs Partially Quoted, and RFQ Review.
- Supplier Quotation Directory, Supplier Quotations To Compare, Expiring Supplier Quotations, and Supplier Quotation Review.
- Purchase Order Directory and PO follow-up queues.
- Purchase Order Follow-up Detail.
- Quote Comparison as the only active report surface.
- Governed native create exceptions for New Purchase Request, New RFQ, New Supplier Quotation, and New Purchase Order.

The Phase 3 closure explicitly deferred reporting and analytics to Phase 4.

## 3. Current Procurement Report Code

Current code only exposes one Procurement report key:

| Route key | Title | Backend | Source | Current state |
| --- | --- | --- | --- | --- |
| `supplier_quotation_comparison` | Quote Comparison | `erp_workspace_ui.procurement_console.report` | ERPNext native `Supplier Quotation Comparison` wrapped through `frappe.desk.query_report.run` | Accepted read-only buyer comparison surface |

Important safety finding: the installed ERPNext native `Supplier Quotation Comparison` report JavaScript includes a `Set Default Supplier` mutation tool. The current Procurement wrapper is therefore the correct approach. Phase 4 must not expose the native report page directly.

## 4. Native ERPNext Report Inventory Verified On Current Site

Verification method: queried the current ERPNext installation on 2026-05-10 using `tabReport`, report role rows, DocPerm rows, and installed report JavaScript files in the running ERPNext backend container.

### 4.1 Buying Reports

| Exact report name | Module | Type | Ref DocType | Key filters found | Purchase Manager access | Purchase User access | Read-only safety | Boundary note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `Purchase Order Analysis` | Buying | Script Report | Purchase Order | Company, From Date, To Date, Project, Purchase Order, Status, Group by PO | Yes, via report role and Purchase User role | Yes | Safe as wrapper | Buyer-owned PO value, item, receive and bill posture. Billing must remain visibility only. |
| `Purchase Analytics` | Buying | Script Report | Purchase Order | Tree Type, based_on DocType, Value or Qty, From Date, To Date, Company, Range | Yes | Yes | Safe only if constrained | Native options include Purchase Receipt and Purchase Invoice, so Phase 4 should not expose raw broad mode. |
| `Purchase Order Trends` | Buying | Script Report | Purchase Order | Include Closed Orders | Yes | Yes | Safe as wrapper | Trend view by supplier/item/group/project is useful, but lower priority than PO Analysis. |
| `Procurement Tracker` | Buying | Script Report | Purchase Order | Company, Cost Center, Project, From Date, To Date | Yes | Yes | Safe as wrapper | Good for demand-to-order coverage across Material Request and PO. |
| `Supplier Quotation Comparison` | Buying | Script Report | Supplier Quotation | Company, From Date, To Date, Item, Supplier, Supplier Quotation, RFQ, Categorize By, Include Expired | Yes | Yes | Not safe raw; safe only as governed wrapper | Native report has Default Supplier mutation tooling. Keep wrapper mutation-free. |
| `Requested Items to Order and Receive` | Buying | Script Report | Material Request | Company, From Date, To Date, Material Request, Item, Group by MR | Yes | Yes | Safe as wrapper | Buyer can review demand-to-order coverage. Receipt portion is Warehouse visibility only. |
| `Item-wise Purchase History` | Buying | Script Report | Purchase Order | Company, From Date, To Date, Item Group, Item, Supplier | Yes | Yes | Safe as wrapper | Strong fit for read-only item price and buying history review. |

### 4.2 Accounts And Downstream Reports Present

| Exact report name | Module | Type | Ref DocType | Key filters found | Purchase Manager access | Purchase User access | Phase 4 position |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `Received Items To Be Billed` | Accounts | Script Report | Purchase Invoice | Company, As on Date, Purchase Receipt | Yes, through Purchase User role | Yes | Optional downstream visibility only; Finance owns billing. |
| `Billed Items To Be Received` | Accounts | Script Report | Purchase Invoice | Company, As on Date, Purchase Invoice | Yes, through Purchase User role | Yes | Optional downstream visibility only; Warehouse owns receiving. |
| `Item-wise Purchase Register` | Accounts | Script Report | Purchase Invoice | From Date, To Date, Item, Item Group, Supplier, Company, Mode of Payment, Group By | Yes, through Purchase User role | Yes | Defer to Finance/Accounting reporting unless owner approves read-only procurement spend review. |
| `Purchase Register` | Accounts | Script Report | Purchase Invoice | From Date, To Date, Supplier, Supplier Group, Company, Mode of Payment, Cost Center, Warehouse, Item Group, Show Ledger View | Yes, through Purchase User role | Yes | Defer to Finance Console. |
| `Accounts Payable` | Accounts | Script Report | Purchase Invoice | Native report filters | Yes, through Purchase User role | Yes | Defer to Finance Console. |
| `Accounts Payable Summary` | Accounts | Script Report | Purchase Invoice | Native report filters | Yes, through Purchase User role | Yes | Defer to Finance Console. |

### 4.3 Reports Not Found As Exact Installed Reports

| Candidate | Current site result | Phase 4 decision |
| --- | --- | --- |
| `Supplier-wise Purchase Register` | Not found as an exact `tabReport` name. | Do not design against this exact report. Use Supplier filters in Purchase Register or Item-wise Purchase History only if later approved. |
| Supplier performance report | No safe current native report verified for this exact surface. | Defer. Avoid inventing scorecards from weak data. |
| Supplier scorecard analytics | ERPNext has Supplier Scorecard documentation, but Phase 3 deferred this area and current safe data/permissions were not proven for reporting. | Defer to a later Supplier Intelligence phase. |

## 5. Enterprise Pattern Review

External systems show consistent procurement analytics patterns:

- SAP S/4HANA purchase order item monitoring focuses on item-level PO status, supplier/material filters, delivery forecast, remaining delivered/invoiced quantity and value, and navigation to item details.
- Microsoft Dynamics positions procurement as the full need-to-payment process, with requisitions, RFQs, supplier selection, PO approval posture, receipt, invoice, payment, vendor catalogs, approved vendor context, and vendor performance reports.
- Oracle procurement analytics emphasizes source-to-settle visibility, spend, supplier risk, operational performance, cycle time, supplier performance, invoice price variance, savings, and cross-functional procurement/finance visibility.
- Odoo Purchase Analysis focuses on buyer-friendly measures such as ordered, received, billed, to-be-billed, total, untaxed total, count, days to confirm, and days to receive, with supplier/item comparison and period comparison.
- ERPNext native Buying Reports already provide Purchase Analytics, Purchase Order Analysis, Purchase Order Trends, Procurement Tracker, requested items, and item-wise purchase history.

Pattern extracted for this ERPNext project:

1. Start with buyer decision reports, not an executive dashboard.
2. Show demand, sourcing, order, item, supplier, receipt posture, and billing posture as a chain.
3. Keep execution actions out of reports.
4. Use native reports where they are safe, but wrap them with productized Procurement copy, filters, drilldowns, and mutation controls.
5. Drill down to productized Phase 3 review/detail pages before native ERP forms.
6. Treat receipt and billing as downstream visibility, not Procurement execution.

Reference sources are listed at the end of this document.

## 6. Phase 4 Business Purpose

Procurement Phase 4 should help a buyer or purchase manager answer:

- What did we order, by supplier, item, project, status, and value?
- What remains open, late, partially received, or not fully billed?
- Which purchase demand has not yet become an order?
- Which suppliers and items drive buying value?
- What are we repeatedly buying from each supplier?
- Are quoted or purchased prices changing for important items?
- Which supplier offers are worth comparing before placing an order?
- What receipt and billing posture should the buyer know, without taking over Warehouse or Finance work?

## 7. Recommended Phase 4 Report Set

Phase 4 should start with a small report catalog. There are now enough meaningful report surfaces to justify a Procurement Reports index page.

### 7.1 Phase 4A, Recommended First Implementation

1. Procurement Reports Index.
2. Purchase Order Analysis.
3. Demand-to-Order Coverage.
4. Item Purchase History and Price Review.
5. Supplier Quotation Comparison enhancement.

This gives buyers a useful reporting layer without crossing into managed forms, Warehouse execution, or Finance execution.

### 7.2 Phase 4B, Later Inside Phase 4 Only If 4A Is Accepted

1. Buying Movement / Purchase Trends.
2. Receipt and Billing Visibility.

These should not block the first Phase 4 reporting release.

## 8. Report Index Decision

Recommendation: add a Procurement Reports Index page.

Reason:

- Phase 3 had one report, so a catalog was unnecessary.
- Phase 4 should add at least four meaningful report surfaces.
- A catalog avoids overloading the sidebar with every report.
- Sidebar can show one `Reports` destination plus the existing high-value `Quote Comparison` shortcut if the owner wants it preserved.
- Overview can show top report shortcuts, but should not become the report catalog.

Proposed routes:

| Surface | Route key | Route path |
| --- | --- | --- |
| Reports Index | `procurement_reports_index` | `/desk/procurement-console-report` or `/desk/procurement-console-report/index` |
| Report Detail | report key | `/desk/procurement-console-report/<report_key>` |

Preferred route behavior: make `/desk/procurement-console-report` the report catalog and keep `/desk/procurement-console-report/supplier-quotation-comparison` for the current Quote Comparison route.

## 9. Proposed Report Contracts

### 9.1 Procurement Reports Index

Route key: `procurement_reports_index`

Title: Procurement Reports

Business goal: provide a compact catalog of approved buyer decision reports.

Target roles:

- Purchase User.
- Purchase Manager.
- Purchase Master Manager only if ERPNext permissions allow the report data.

Filters: none for the catalog itself.

Metrics and sections:

- Sourcing review: Quote Comparison.
- Order review: Purchase Order Analysis.
- Demand coverage: Demand-to-Order Coverage.
- Item and supplier price review: Item Purchase History.
- Later: Buying Movement and Downstream Visibility.

Drilldown targets:

- Report cards route to `/desk/procurement-console-report/<report_key>`.
- No native ERP report route as the default target.

Backend source:

- Custom catalog payload from report registry.

State kinds:

- `ready`: at least one visible report is allowed.
- `restricted`: user has no Procurement report access.
- `empty`: no reports visible after role filtering.
- `unavailable`: report registry cannot resolve Phase 4 catalog.
- `error`: only real technical failure.

Explicitly not allowed:

- Native report links as primary cards.
- Finance-owned reports presented as Procurement-owned execution.

### 9.2 Purchase Order Analysis

Route key: `purchase_order_analysis`

Title: Purchase Order Analysis

Business goal: analyze ordered value, open posture, receipt posture, and billing posture by PO, supplier, item, and status.

Target roles:

- Purchase User and Purchase Manager.
- Finance/Executive only if they also have Purchase access.

Filters:

- Date From.
- Date To.
- Purchase Order.
- Supplier.
- Item.
- Project, optional if data exists.
- Status.
- Group by Purchase Order.
- Company hidden/defaulted for single-company context.

Metrics/KPIs:

- Orders in view.
- Ordered amount.
- Open receiving quantity/value.
- Open billing quantity/value.
- Late/open order count, if derived safely from PO item schedule dates.

Tables/charts:

- PO summary table.
- Item-level table for quantity, received, billed, amount, supplier, required date, status.
- Optional small trend chart by month only if native payload is stable.

Drilldown targets:

- Purchase Order -> `/desk/procurement-console-po-follow-up/<po>`.
- Supplier -> `/desk/procurement-console-supplier/<supplier>`.
- Item -> `/desk/procurement-console-item/<item>`.

Backend source:

- Preferred first implementation: governed native wrapper over ERPNext `Purchase Order Analysis`, with custom post-processing for metrics and productized drilldowns.
- Custom backend may be needed for schedule-date and PO item-level safety.

State kinds:

- `ready`: rows returned.
- `empty`: no PO data for selected filters.
- `restricted`: missing Procurement access or Purchase Order read/report permission.
- `unavailable`: native report unavailable, disabled, or missing required fields.
- `error`: report execution failure.

Explicitly not allowed:

- Approve/reject/submit/cancel/amend/close.
- Receive or bill actions.
- Native Purchase Order form as primary row target.

### 9.3 Demand-to-Order Coverage

Route key: `demand_to_order_coverage`

Title: Demand-to-Order Coverage

Business goal: show which purchase demand has been ordered, partially ordered, or still needs buyer action.

Target roles:

- Purchase User and Purchase Manager.

Filters:

- Date From.
- Date To.
- Material Request.
- Item.
- Supplier if safely derivable.
- Status.
- Requested-by or department only if present and permission-safe.
- Company hidden/defaulted.

Metrics/KPIs:

- Request lines in view.
- Not ordered lines.
- Partially ordered lines.
- Ordered but not received posture, visibility only.
- Age of oldest open request line.

Tables/charts:

- Material Request line table with requested qty, ordered qty, received qty, remaining qty, item, required date, linked POs.
- Optional coverage bar: requested -> ordered -> received visibility.

Drilldown targets:

- Material Request -> `/desk/procurement-console-purchase-request-review/<mr>`.
- Purchase Order -> `/desk/procurement-console-po-follow-up/<po>`.
- Item -> `/desk/procurement-console-item/<item>`.

Backend source:

- Native `Procurement Tracker` plus selected fields from `Requested Items to Order and Receive` if needed.
- Prefer a custom wrapper module that normalizes both native report payloads into one buyer-friendly shape.

State kinds:

- `ready`, `empty`, `restricted`, `unavailable`, `error` as above.

Explicitly not allowed:

- Create PO from report.
- Receive stock from report.
- Material Request approval or cancellation from report.

### 9.4 Item Purchase History and Price Review

Route key: `item_purchase_history`

Title: Item Purchase History

Business goal: help buyers review what has been bought, from whom, at what rate, and whether recent prices need attention.

Target roles:

- Purchase User and Purchase Manager.

Filters:

- Date From.
- Date To.
- Item.
- Item Group.
- Supplier.
- Company hidden/defaulted.

Metrics/KPIs:

- Items in view.
- Suppliers in view.
- Purchase value.
- Average rate.
- Highest/lowest recent rate, if safely derived from returned rows.

Tables/charts:

- Item/supplier purchase history table.
- Optional rate movement mini chart by item and supplier.
- Optional recent quote vs order comparison only if data is reliable.

Drilldown targets:

- Item -> `/desk/procurement-console-item/<item>`.
- Supplier -> `/desk/procurement-console-supplier/<supplier>`.
- Purchase Order -> `/desk/procurement-console-po-follow-up/<po>`.

Backend source:

- Native ERPNext `Item-wise Purchase History` wrapper.
- Do not use `Item Price` mutation or default supplier updates.

State kinds:

- `ready`, `empty`, `restricted`, `unavailable`, `error`.

Explicitly not allowed:

- Item Price creation/update.
- Default Supplier update.
- Item create/edit.
- Supplier create/edit.

### 9.5 Supplier Quotation Comparison Enhancement

Route key: `supplier_quotation_comparison`

Title: Quote Comparison

Business goal: compare supplier offers by item, supplier, RFQ, validity, price, and quote posture.

Target roles:

- Purchase User and Purchase Manager.

Filters:

- Date From.
- Date To.
- Item.
- Supplier.
- Supplier Quotation.
- RFQ.
- Categorize by Supplier or Item.
- Expired filter.
- Company hidden/defaulted.

Metrics/KPIs:

- Quotations in view.
- Suppliers represented.
- Items represented.
- Expiring/expired validity rows.
- Best price rows, if calculated transparently and read-only.

Tables/charts:

- Supplier offer comparison table.
- Optional grouped item comparison card when one item is selected.
- Optional quote validity warning strip.

Drilldown targets:

- Supplier Quotation -> `/desk/procurement-console-supplier-quotation-review/<sq>`.
- RFQ -> `/desk/procurement-console-rfq-review/<rfq>`.
- Supplier -> `/desk/procurement-console-supplier/<supplier>`.
- Item -> `/desk/procurement-console-item/<item>`.

Backend source:

- Continue current governed wrapper over ERPNext `Supplier Quotation Comparison`.
- Suppress native `Set Default Supplier` and any Item Price/default supplier mutation tools.

State kinds:

- `ready`, `empty`, `restricted`, `unavailable`, `error`.

Explicitly not allowed:

- Set Default Supplier.
- Item Price update.
- Create Purchase Order from comparison.
- Native Supplier Quotation mutation tools.

### 9.6 Buying Movement / Purchase Trends

Route key: `purchase_trends`

Title: Purchase Trends

Business goal: show buying movement over time by supplier, item, item group, supplier group, or project.

Recommended timing: Phase 4B, after Purchase Order Analysis is stable.

Filters:

- Fiscal year or date range.
- Supplier.
- Supplier Group.
- Item.
- Item Group.
- Project.
- Include Closed Orders.
- Company hidden/defaulted.

Metrics/KPIs:

- Purchase value trend.
- Purchase order count trend.
- Supplier and item concentration.

Tables/charts:

- Trend chart by month/quarter.
- Breakdown table by selected dimension.

Backend source:

- Native `Purchase Order Trends` or a constrained `Purchase Analytics` wrapper locked to Purchase Order data only.

Explicitly not allowed:

- Raw `Purchase Analytics` mode that switches to Purchase Receipt or Purchase Invoice without clear downstream-visibility labeling.
- Finance-owned spend ledger presentation.

### 9.7 Receipt and Billing Visibility

Route key: `receipt_billing_visibility`

Title: Receipt and Billing Visibility

Business goal: show downstream posture that buyers need to understand, without making Procurement own Warehouse or Finance execution.

Recommended timing: Phase 4B or later. Do not block Phase 4A.

Filters:

- As on Date.
- Purchase Order.
- Supplier.
- Item.
- Company hidden/defaulted.

Metrics/KPIs:

- Received not fully billed.
- Billed not fully received.
- Open receiving posture.
- Open billing posture.

Tables/charts:

- Visibility table grouped by PO and supplier.
- Links to productized PO Follow-up Detail.

Backend source:

- Prefer existing Phase 3 PO follow-up data plus native Accounts reports only as supporting sources.
- Native candidates: `Received Items To Be Billed` and `Billed Items To Be Received`.

Boundary note:

- Warehouse owns receiving.
- Finance owns invoices, payables, and payment.
- This report must use visibility language only.

Explicitly not allowed:

- Create Purchase Receipt.
- Create Purchase Invoice.
- Payment Entry.
- Accounts Payable actions.

## 10. Reports To Defer Or Exclude

| Candidate | Decision | Reason |
| --- | --- | --- |
| Broad Purchase Analytics dashboard | Defer | Native report can include Purchase Receipt and Purchase Invoice modes. Needs stricter ownership design. |
| Purchase Register | Defer to Finance Console | Invoice/accounting-owned. |
| Item-wise Purchase Register | Defer unless owner approves read-only spend review | Ref DocType is Purchase Invoice; risks Finance ownership drift. |
| Accounts Payable / Summary | Exclude from Procurement Phase 4 | Finance-owned settlement and exposure. |
| Supplier Scorecard / Supplier Performance | Defer | Needs data quality, scoring policy, and owner-approved supplier governance. |
| Supplier portal/email reporting | Exclude | Not Phase 4 reporting scope. |
| Managed create/edit form analytics | Exclude | Phase 5 owns Managed Procurement Forms. |

## 11. Permission Rules

Baseline roles:

- `Purchase User` can access Phase 4 reports only when ERPNext read/report permissions allow the referenced DocTypes.
- `Purchase Manager` can access Phase 4 reports and manager-level report views when ERPNext permissions allow them.
- `Purchase Master Manager` should not automatically bypass report-level checks; allow only if Procurement access and referenced DocType permissions are valid.
- Finance Lead Approver and Executive Approver remain restricted unless they also hold Purchase roles.
- Non-procurement users receive `restricted` on direct report routes.
- Guest receives a permission error, not an anonymous report payload.

Every report backend must check:

1. Procurement access.
2. Referenced DocType read/report permission.
3. Native report existence and enabled state when using a native wrapper.
4. Row-level visibility through permission-aware queries or native report permission behavior.

## 12. Implementation Architecture Proposal

Do not implement until owner approval.

### 12.1 Backend Modules

Keep `erp_workspace_ui.procurement_console.report` as the whitelisted facade and split report builders into small domain modules:

- `erp_workspace_ui.procurement_console.reports.__init__`
- `erp_workspace_ui.procurement_console.reports.registry`
- `erp_workspace_ui.procurement_console.reports.native_runner`
- `erp_workspace_ui.procurement_console.reports.report_index`
- `erp_workspace_ui.procurement_console.reports.purchase_order_analysis`
- `erp_workspace_ui.procurement_console.reports.demand_to_order`
- `erp_workspace_ui.procurement_console.reports.item_purchase_history`
- `erp_workspace_ui.procurement_console.reports.quote_comparison`
- `erp_workspace_ui.procurement_console.reports.downstream_visibility`, only if Phase 4B is approved.

### 12.2 Whitelisted Entrypoints

Use existing naming patterns and avoid Sales method names:

- `erp_workspace_ui.procurement_console.report.get_procurement_console_report_context`
- `erp_workspace_ui.procurement_console.report.get_procurement_report_index_context`
- `erp_workspace_ui.procurement_console.report.get_procurement_report_payload`, only if the shared report shell needs a generic payload refresh method.

### 12.3 Report Registry Structure

Each report registry entry should declare:

- `report_key`
- `title`
- `summary`
- `native_report_name`, if any
- `ref_doctype`
- `source_kind`: `native_wrapper` or `custom_payload`
- `phase`: `4A` or `4B`
- `filters`
- `metrics`
- `columns`
- `drilldown_targets`
- `roles`
- `required_doctype_permissions`
- `state_policy`
- `forbidden_actions`
- `ownership_boundary`

### 12.4 Frontend And Shared Shells

Use the existing shared report shell first.

Allowed frontend work after approval:

- Extend Procurement report controller only to resolve new report keys.
- Add report index rendering through shared console/report catalog patterns.
- Add chart/table payloads through shared report components.
- Add no page-local filter, table, button, or chart pattern unless the shared shell cannot support a named need.

If shared report shell or shared CSS is touched, Sales freeze protection is mandatory.

### 12.5 Route Keys

Recommended report keys:

- `procurement_reports_index`
- `purchase_order_analysis`
- `demand_to_order_coverage`
- `item_purchase_history`
- `supplier_quotation_comparison`
- `purchase_trends`, Phase 4B.
- `receipt_billing_visibility`, Phase 4B.

### 12.6 Action Classifications

Allowed report actions:

- Apply filters.
- Reset filters.
- Refresh report.
- Open productized Procurement detail/review page.
- Back to Reports.
- Back to Procurement Console.

Forbidden report actions:

- Create, edit, submit, cancel, amend, close, approve, reject.
- Receive, bill, pay.
- Item Price update.
- Default Supplier update.
- Native report mutation buttons.
- Raw native ERPNext form as primary row drilldown.

Secondary governed native form access may exist only in review/detail pages where Phase 3 already permits it, not in report table primary actions.

### 12.7 Governance Manifest Additions

Add Phase 4 report surfaces to the governance manifest as productized report routes.

Each route should classify:

- Report route ownership: Procurement.
- Native wrapper source, if any.
- Allowed target kinds.
- Forbidden actions.
- Native exception policy: none for report pages, except the already documented detail-page secondary `Open ERP Form` actions.

## 13. Testing Plan For Later Implementation

### 13.1 Python Tests

Add or extend tests for:

- Report registry keys and route uniqueness.
- Native report availability handling.
- State kinds: `ready`, `empty`, `restricted`, `unavailable`, `error`.
- Purchase Manager and Purchase User access.
- Non-procurement restricted direct route.
- Guest permission error.
- Supplier Quotation Comparison mutation suppression.
- Productized drilldown targets for PO, Supplier, Item, RFQ, Supplier Quotation, and Material Request.
- Finance/Executive restricted unless they also have Purchase roles.
- No Phase 5 managed form routes accidentally enabled.

### 13.2 JavaScript Checks

Run `node --check` for every touched JavaScript file.

If shared report/list/child/console runtime is touched, run the Sales freeze protection gate.

### 13.3 Browser Smoke

Use Docker Playwright runner only.

Required smoke for Purchase Manager and Purchase User:

- Reports Index loads.
- Each Phase 4A report loads.
- Apply, Reset, Refresh work in place.
- Link autocomplete works for Supplier, Item, Purchase Order, Material Request, RFQ, and Supplier Quotation filters where data exists.
- Drilldowns route to productized Phase 3 detail/review pages.
- No raw native report mutation tools appear.
- Supplier Quotation Comparison does not show Set Default Supplier.
- Company filter is hidden/defaulted in single-company mode.
- Direct restricted routes return restricted for non-procurement users.
- No duplicate headers, shell stacking, horizontal overflow, or page JS errors.

### 13.4 Sales Freeze Gate

Mandatory if implementation touches:

- Shared CSS.
- Shared workspace runtime.
- Shared report shell.
- Shared list shell.
- Shared chart/table components.
- Workspace registry.
- Governance manifest.
- Sales files.

Command:

```bash
npm --prefix ui_smoke run test:sales-freeze-protection
```

## 14. Phase 4 Acceptance Gates

Before owner freeze consideration:

1. `python3 -m compileall erp_workspace_ui`
2. `PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'`
3. `node --check` for touched JavaScript.
4. `git diff --check HEAD`.
5. Procurement Phase 4 Docker smoke for Purchase Manager.
6. Procurement Phase 4 Docker smoke for Purchase User.
7. Restricted direct route smoke for non-procurement user if credentials are available.
8. Sales freeze protection gate if shared files were touched.
9. Manual owner review of report usefulness, copy, ownership boundaries, and drilldown safety.
10. No live alignment until source gates pass.

## 15. Recommended Implementation Sequence After Approval

1. Add report registry and Reports Index with only existing Quote Comparison card.
2. Add Purchase Order Analysis wrapper and drilldowns.
3. Add Demand-to-Order Coverage using Procurement Tracker and Requested Items sources.
4. Add Item Purchase History and Price Review read-only wrapper.
5. Enhance Quote Comparison metrics and drilldowns while keeping mutation tools suppressed.
6. Run owner review.
7. Only then evaluate Purchase Trends and Receipt/Billing Visibility for Phase 4B.

## 16. Key Risks

- Native report payloads may be wide, slow, or inconsistent across ERPNext versions.
- Supplier Quotation Comparison has native mutation tooling that must remain suppressed.
- Purchase Analytics can cross into Purchase Receipt and Purchase Invoice ownership if exposed raw.
- Accounts reports are accessible to Purchase roles on this site, but business ownership still belongs to Finance.
- Receipt and billing posture can be useful to buyers but must not become Warehouse or Finance execution.
- Company filters should be defaulted/hidden for current single-company UX, while backend must still pass company safely to native reports.
- Report drilldowns must avoid raw native ERPNext leaks and use productized Phase 3 pages first.
- Shared report shell improvements may require Sales freeze protection.

## 17. References

- ERPNext Buying Reports: https://docs.frappe.io/erpnext/buying_reports
- SAP Help, Monitor Purchase Order Items: https://help.sap.com/docs/SAP_S4HANA_CLOUD/0e602d466b99490187fcbb30d1dc897c/82f1e2574096f432e10000000a441470.html
- SAP Help, Purchase Order Item Monitor CDS view: https://help.sap.com/docs/SAP_S4HANA_CLOUD/0e602d466b99490187fcbb30d1dc897c/9463806a0123453ca47f260f6105ef98.html
- Microsoft Dynamics 365 Procurement and sourcing overview: https://learn.microsoft.com/en-us/dynamics365/supply-chain/procurement/procurement-sourcing-overview
- Microsoft Dynamics 365 Purchase requisition overview: https://learn.microsoft.com/en-us/dynamics365/supply-chain/procurement/purchase-requisitions-overview
- Oracle Fusion Cloud Procurement overview: https://docs.oracle.com/en/cloud/saas/procurement/25c/fainp/about-oracle-fusion-cloud-procurement.html
- Oracle Procurement Analytics product tour: https://www.oracle.com/business-analytics/fusion-erp-analytics/procurement-product-tour/
- Odoo Purchase Analysis report: https://www.odoo.com/documentation/19.0/applications/inventory_and_mrp/purchase/advanced/analyze.html