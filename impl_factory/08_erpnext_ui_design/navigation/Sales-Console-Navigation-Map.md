# Sales Console Navigation Map

Status: detailed navigation and page-family design for `Sales Console`  
Scope: workspace-to-page flow, page ownership, page types, and child-page behavior  
Source authority: [UI-Design.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/UI-Design.md) and [Sales-Console-Design.md](/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/08_erpnext_ui_design/Sales-Console-Design.md)

## 1. Purpose

This document defines the `Sales Console` as a workspace family, not just a single landing page.

That means it answers:

1. what the user opens from `Sales Console`
2. which child pages belong to the sales family
3. which pages are sales-owned, shared, or finance-owned
4. what kind of page each target should be
5. how AI should assist without taking over navigation

## 2. Core Design Decision

The `Sales Console` is the parent workspace for sales execution.

It should not try to contain the full transaction workflow inside one screen.

The correct enterprise structure is:

1. `Sales Console` as the daily command page
2. full transaction pages for core documents
3. focused worklist pages for queues and follow-up
4. review pages for blockers and insight
5. read-only shared pages where sales needs visibility into finance or fulfillment state

## 3. Working Structure

The simple operating flow is:

1. user signs in
2. user lands on `Sales Console`
3. user sees context, quick actions, work queue, blockers, and AI summary
4. user clicks into the right child page
5. user completes the transaction, review, or follow-up task
6. user returns to `Sales Console` for the next action

This keeps the workspace simple while still supporting serious enterprise work.

## 4. Page Type Model

The `Sales Console` family should use five page types.

### 4.1 Workspace Home

Use for:

1. daily entry point
2. quick actions
3. work queue
4. operational insight
5. compact AI assist

Example:

1. `Sales Console`

### 4.2 Full Transaction Page

Use for:

1. documents that require validation
2. line-item handling
3. workflow state
4. approval visibility
5. full ERP audit behavior

Examples:

1. `Opportunity Form`
2. `Quotation Form`
3. `Sales Order Form`

### 4.3 Worklist Page

Use for:

1. a filtered operational queue
2. follow-up work
3. aging review
4. exception handling

Examples:

1. `Quotation Follow-Up Worklist`
2. `Open Orders Review`
3. `Customer Follow-Up Worklist`

### 4.4 Record Review Page

Use for:

1. reading a master record
2. reviewing transaction history
3. understanding current status before action

Examples:

1. `Customer Page`
2. `Item Page`
3. `Customer Commercial Snapshot`

### 4.5 Report Or Insight Page

Use for:

1. historical analysis
2. trend review
3. management visibility
4. deeper investigation after the workspace summary

Examples:

1. `Sales Analytics`
2. `Customer-wise Sales History`
3. `Quotation Conversion Review`

## 5. Primary Navigation Map

### 5.1 Quick Actions

`New Opportunity` -> `Opportunity Form`

1. page type: full transaction page
2. ownership: sales
3. behavior: open full form page
4. AI role: optional customer and item briefing only

`New Quotation` -> `Quotation Form`

1. page type: full transaction page
2. ownership: sales
3. behavior: open full form page
4. prefill options: branch, territory, customer, showroom mode
5. AI role: approval-risk and follow-up hints only

`New Sales Order` -> `Sales Order Form`

1. page type: full transaction page
2. ownership: sales
3. behavior: open full form page
4. prefill options: branch, customer, quotation context when applicable
5. AI role: order-risk and next-step hints only

`Open Customer` -> `Customer Page`

1. page type: record review page
2. ownership: shared, sales-primary usage
3. behavior: open search or direct customer record
4. AI role: compact customer briefing

`Open Item` -> `Item Page`

1. page type: record review page
2. ownership: shared
3. behavior: open item search or direct item record
4. AI role: none by default

### 5.2 Work Queue Navigation

`Quotations Waiting For Action` -> `Quotation Follow-Up Worklist`

1. page type: worklist page
2. ownership: sales
3. emphasis: aging, pending customer reply, expiring soon, needs revision

`Open Quotations Nearing Expiry` -> `Expiring Quotations Worklist`

1. page type: worklist page
2. ownership: sales
3. emphasis: follow-up urgency and renewal

`Sales Orders Pending Fulfillment` -> `Open Orders Review`

1. page type: worklist page
2. ownership: sales with shared fulfillment visibility
3. emphasis: order status, pending dispatch, transfer dependency

`Orders Blocked By Approval` -> `Blocked Commercial Documents Review`

1. page type: worklist page
2. ownership: shared
3. emphasis: waiting on approval, credit, discount, or control review

`Customer Follow-Up Tasks` -> `Customer Follow-Up Worklist`

1. page type: worklist page
2. ownership: sales
3. emphasis: promised callbacks, quote chase, inactive accounts

`Overdue Or At-Risk Commercial Items` -> `Commercial Risk Review`

1. page type: worklist page
2. ownership: shared
3. emphasis: delayed conversions, risk flags, credit concerns, approval friction

### 5.3 Insight And Report Navigation

`Quotations Awaiting Approval` -> `Quotation Approval Review`

1. page type: worklist or review page
2. ownership: shared
3. note: sales can view status, but approval authority follows governance

`Open Orders` -> `Open Orders Review`

1. page type: worklist page
2. ownership: shared

`Orders With Credit-Risk Flags` -> `Credit Exposure Review`

1. page type: review page
2. ownership: finance-owned, sales-visible where permitted
3. note: sales should see commercial impact, not full finance administration

`Customers Needing Follow-Up Today` -> `Customer Follow-Up Worklist`

1. page type: worklist page
2. ownership: sales

`Branch Sales Snapshot` -> `Branch Sales Snapshot Report`

1. page type: report page
2. ownership: shared

`Quotation-To-Order Conversion Trend` -> `Conversion Review`

1. page type: report page
2. ownership: sales

## 6. Sales Family Page Portfolio

### 6.1 Sales-Owned Core Pages

These belong directly to the `Sales Console` family.

1. `Opportunity Form`
2. `Quotation Form`
3. `Sales Order Form`
4. `Quotation Follow-Up Worklist`
5. `Expiring Quotations Worklist`
6. `Customer Follow-Up Worklist`
7. `Open Orders Review`
8. `Commercial Risk Review`
9. `Conversion Review`

### 6.2 Shared Visibility Pages

These support sales work but are not exclusively owned by sales.

1. `Customer Page`
2. `Item Page`
3. `Customer Commercial Snapshot`
4. `Quotation Approval Review`
5. `Blocked Commercial Documents Review`
6. `Branch Sales Snapshot Report`
7. fulfillment status views linked to warehouse and operations state

### 6.3 Finance-Owned Pages

These should not be primary `Sales Console` actions.

1. `Sales Invoice`
2. `Payment Entry`
3. `Accounts Receivable Review`
4. `Credit Control Administration`
5. `Receivable Aging And Collection Review`

Important rule:

1. `Sales Invoice` is primarily a finance and accounting document
2. sales users may need status visibility
3. sales users should not own invoice administration by default
4. any exception must be explicitly approved by business governance

## 7. Page Design Standards For The Sales Family

### 7.1 Transaction Pages

Pages:

1. `Opportunity Form`
2. `Quotation Form`
3. `Sales Order Form`

Structure:

1. header with document identity, status, branch, and customer
2. action bar for save, submit, print, or permitted workflow actions
3. commercial context strip for approval, credit, stock, or pricing warning
4. core form area for transaction editing
5. compact AI support area, secondary and collapsible

Behavior:

1. open as full page, not a modal
2. preserve full ERPNext validation and auditability
3. support return to `Sales Console`
4. support prefilled context when launched from the workspace

### 7.2 Worklist Pages

Pages:

1. `Quotation Follow-Up Worklist`
2. `Expiring Quotations Worklist`
3. `Customer Follow-Up Worklist`
4. `Open Orders Review`
5. `Commercial Risk Review`

Structure:

1. page header with queue meaning
2. filter bar for branch, user, aging band, customer, status
3. high-signal list or table
4. row actions for open, follow-up, escalate, or review
5. AI summary block for prioritization when useful

Behavior:

1. default to the user’s scope
2. sort by urgency, not alphabetically
3. expose exceptions before neutral items
4. make it easy to open the document in one click

### 7.3 Record Review Pages

Pages:

1. `Customer Page`
2. `Item Page`
3. `Customer Commercial Snapshot`

Structure:

1. master record summary
2. recent transaction timeline
3. active quotation and order visibility
4. branch or territory context
5. compact AI briefing where high-value

Behavior:

1. optimized for preparation before sales action
2. read-heavy and action-light
3. should clearly show what the user can do next

### 7.4 Report And Insight Pages

Pages:

1. `Sales Analytics`
2. `Customer-wise Sales History`
3. `Branch Sales Snapshot Report`
4. `Conversion Review`

Structure:

1. summary metrics first
2. drill-down second
3. export or print actions where relevant
4. no clutter from transaction-creation actions

Behavior:

1. used for review, not daily transaction entry
2. should stay linked from the console, not replace it as the main home

## 8. Role And Access Guidance

### 8.1 Sales Executive

Main pages:

1. `Sales Console`
2. `Quotation Form`
3. `Customer Follow-Up Worklist`
4. `Quotation Follow-Up Worklist`
5. `Customer Page`

Should usually not own:

1. finance document control
2. broad credit administration
3. invoice management

### 8.2 Sales Supervisor

Main pages:

1. all Sales Executive pages
2. `Open Orders Review`
3. `Blocked Commercial Documents Review`
4. `Quotation Approval Review`
5. `Commercial Risk Review`

### 8.3 Key Account Sales

Main pages:

1. `Sales Console`
2. `Customer Page`
3. `Quotation Form`
4. `Sales Order Form`
5. `Customer Commercial Snapshot`

Emphasis:

1. account-level visibility
2. customer history
3. controlled commercial exception awareness

### 8.4 Showroom-Focused Sales User

Main pages:

1. `Sales Console` in showroom mode
2. `Quotation Form`
3. `Sales Order Form`
4. `Item Page`

Restrictions:

1. narrower stock visibility
2. simpler layout
3. fewer analytics and management review surfaces

## 9. AI Navigation Role

AI should help the user choose the right next page, but should not become the primary navigation mechanism.

Recommended AI roles:

1. suggest which queue deserves attention now
2. summarize a customer before opening the record
3. warn about approval or credit context before opening a document
4. explain why a document appears in a blocker queue

Avoid:

1. forcing users to ask chat where to go
2. replacing normal buttons with AI prompts
3. hiding workflow logic inside AI text

## 10. Final Design Judgment

The `Sales Console` family should be designed as:

1. one strong workspace home
2. a small number of clear transaction pages
3. a high-value set of worklist pages
4. controlled shared visibility into finance and operations
5. finance ownership for `Sales Invoice`, with sales visibility only where justified

This gives the business a cleaner, safer, and more enterprise-grade structure than treating all commercial pages as one undifferentiated sales area.
