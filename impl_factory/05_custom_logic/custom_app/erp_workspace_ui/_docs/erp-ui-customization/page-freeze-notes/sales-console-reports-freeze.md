# Freeze Note: Sales Console Reports

Date: 2026-04-21

Last implementation alignment: 2026-05-03
Final freeze decision: 2026-05-03

Status:

- Frozen after owner visual/business acceptance

Automated browser proof:

- Docker Playwright runner passed role smoke and Sales Order Analysis smoke for Sales Manager and Sales User on 2026-05-02
- full live report route probing passed on 2026-05-03 for role-visible report catalogs
- hidden manager reports return restricted states for Sales User direct URLs
- owner visual/business acceptance is recorded on 2026-05-03

Scope:

- Sales Console report family
- `Sales Analytics`
- `Sales Order Analysis`
- `Trend Analysis`
- `Lost Quotations`
- `Collections Status`
- `Item-wise Sales History`

Not in scope:

- standalone `Sales Dashboard`; removed before freeze because it overlapped with Sales Analytics and did not yet provide enough distinct enterprise value

## Freeze decision

Sales Console reports are accepted as the current reporting layer for the sales workspace.

Final freeze marker: `sales-console-freeze-v1`

They are approved because they now behave like focused commercial review surfaces instead of raw ERP report dumps:

- each page uses the same productized report shell
- filters are reduced to business-useful controls
- KPI cards are restrained and readable
- tables are aligned to operational review instead of generic query output
- report meanings are now separated more truthfully across sales value, order execution, quotation movement, losses, collections, and item history

## What is accepted

### 1. Report architecture is coherent

- the report family now follows one shared shell instead of page-by-page decorative patterns
- filter bands, KPI cards, summary sections, and result tables use a stable common structure
- the report layer is now part of the Sales Console product surface, not a side collection of unrelated pages

### 2. Sales Analytics is accepted as the management baseline

- it is now a focused customer-value report, not a noisy generic analytics screen
- the page keeps the selected reporting window readable through restrained KPI and period-trend summaries
- customer detail is acceptable for management review without forcing extra chart complexity

### 3. Sales Order Analysis is accepted as the execution report

- it correctly emphasizes operational posture instead of duplicating broad sales analytics
- open execution, overdue delivery, pending bill, and visible order value are the right commercial control signals
- quantity-to-deliver is accepted because it supports execution review directly
- the default opening window is now a rolling 30-day operating window, not month-to-date, so the page should open with useful recent orders even early in a new month

### 4. Trend Analysis and Lost Quotations are accepted as commercial review pages

- `Trend Analysis` replaces the visible `Quotation Trends` card so invoice, order, and quotation movement can be reviewed from one controlled page
- the default trend source is Sales Invoice because billed value is the final commercial truth
- Quotation remains available inside the Document Type filter and through the legacy `quotation_trends` route for backward compatibility
- `Lost Quotations` is accepted as the loss-pattern page, including grouped commercial review by reason or competitor where data supports it
- navigation was intentionally limited where ERP destinations are not trustworthy or business-useful

### 5. Collections Status is accepted instead of payment-term reporting

- the original payment-terms view was not the right business truth for sales follow-up
- the current page now reports real invoice settlement and receivable exposure, which is the correct commercial surface
- overdue and open invoice posture are now expressed in a way sales and management can use

### 6. Item-wise Sales History is accepted as monthly item review

- the page was corrected from an over-wide line-history view into a monthly item-customer summary
- monthly grouping, order counts, and compact numeric formatting are accepted as the right tradeoff for usability
- the page is now suitable for item and customer discussion without behaving like a raw transaction dump

## Accepted deferred items

- later AI-assisted interpretation layer for reports if it is implemented as a separate, deliberate stream
- future comparison features such as period-vs-period overlays only if they are added without bloating the core report shell
- one final cross-report typography and spacing pass only if it is shared and low-risk
- later data-quality cleanup where ERP master data limits what some reports can express, such as incomplete lost-reason or competitor inputs
- final manual browser acceptance remains the owner checkpoint before declaring the report family fully frozen

## Security and Route Notes

- report cards are now the authority for role-visible Sales Console reports
- direct URLs to hidden report keys return a restricted Sales Console state instead of relying only on native report permission or hidden navigation
- legacy `quotation_trends` remains allowed only through the visible `Trend Analysis` access key and opens Trend Analysis with Quotation selected
- legacy `payment_terms_status_sales_order` maps through the visible `Collections Status` access key

## Reopen conditions

Reopen only if:

- report totals stop matching live ERP data
- filter inputs become misleading or inconsistent across the report family
- a report drifts back into raw-query behavior instead of the shared productized shell
- collections truth regresses back toward payment-term proxies instead of actual invoice settlement
- item history loses monthly grouping clarity or becomes horizontally unusable again
