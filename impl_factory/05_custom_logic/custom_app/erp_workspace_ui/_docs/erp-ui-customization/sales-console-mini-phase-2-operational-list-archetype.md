# Sales Console Mini-Phase 2 Operational List Archetype

Status: implemented shared worklist foundation
Date: 2026-04-17
Last updated: 2026-04-23
Source of truth: `sales_console/worklist.py`, `page/sales_console_worklist/sales_console_worklist.js`, and `public/js/runtime/list_page/list_page_shell.js`

## 1. Purpose

This note defines the shared operational-list standard now used by the Sales Console worklist family.

It exists so that:

1. operational lists are built once as a reusable enterprise pattern
2. later pages are implemented as variants, not as isolated page designs
3. the list family stays visually and behaviorally aligned with the frozen Sales Console detail pages
4. later list variants stay thin data variants over one stable shell

## 2. Core Decision

The remaining Sales Console list pages should not be implemented as raw native ERP list pages.

They also should not be implemented by stretching the child document page renderer beyond its purpose.

The correct architecture is:

1. keep document execution pages on the existing `erpWorkspaceUiChildPage` shell
2. introduce a dedicated shared list runtime for queue, review, and report surfaces
3. keep both systems inside the same visual language, spacing system, and tone model
4. treat each page as a thin data variant over one shared list shell

Mini-Phase 2 established this shared runtime surface:

1. `erpWorkspaceUiListPage`

Current implementation also includes:

1. route page `sales-console-worklist`
2. backend method `erp_workspace_ui.sales_console.worklist.get_sales_console_worklist_context`
3. queue-key routing through `/desk/sales-console-worklist/<queue-key>`
4. filter payload support for productized list controls
5. row action targets for opening linked ERP records
6. guarded state for unsupported or missing queue keys

## 3. Where The Archetype Fits

This archetype is for:

1. quotation follow-up worklists
2. sales-order fulfillment worklists
3. customer follow-up task worklists
4. invoice outstanding worklists
5. return and exception worklists
6. approval-review worklists
7. customer and item review entry lists

It is not for:

1. full transaction forms such as Quotation, Sales Order, Delivery Note, or Sales Invoice
2. draft create flows already handled by the child-page form architecture
3. Inquiry, which is already productized as part of Sales Console home
4. report pages, which use a separate report-family runtime direction

## 4. Enterprise List Structure

Every operational list page should follow the same five-layer structure.

### 4.1 Summary Band

Purpose:

1. define what this list is
2. explain the business scope in one sentence
3. expose a small number of trusted summary facts
4. show page-level state chips without turning the page into a dashboard

Required content:

1. kicker
2. title
3. subtitle
4. state chips when relevant
5. summary facts such as queue size, overdue count, or ownership scope

Rule:

1. no decorative chart in the header
2. no large hero artwork
3. summary must remain operational, not promotional

### 4.2 Control Band

Purpose:

1. keep the active filter scope explicit
2. support search and list actions
3. allow users to change operating context without leaving the page

Required content:

1. visible active filter chips
2. optional quick scope chips such as team, mine, overdue, expiring, blocked
3. form controls when the page is a directory-style worklist, such as Customers or Items
4. page actions such as apply, reset, refresh, export, or save view when relevant

Rule:

1. filter state must be readable at a glance
2. filter controls must not feel like a report-builder
3. the control band should stay lighter than the summary band

### 4.3 Signal Strip

Purpose:

1. surface a few business signals that change user priority inside the same list
2. support queue triage before reading rows one by one

Typical signals:

1. overdue items
2. expiring soon
3. blocked by approval
4. partially delivered
5. settlement at risk

Rule:

1. this strip is optional
2. only use it when signals materially change user priority
3. do not duplicate the same meaning already shown in the summary band

### 4.4 Results Surface

Purpose:

1. present the trusted operational table
2. keep row hierarchy readable
3. support rapid scanning and opening of records

Required content:

1. result title and short note
2. result count or scope note
3. table-first layout
4. row actions that are operationally true

Rule:

1. table beats decorative cards for the first implementation wave
2. row hierarchy must show document identity first, then state, then timing, then ownership, then next action
3. row actions should be few and explicit

### 4.5 State Surface

Purpose:

1. keep loading, empty, restricted, and error states enterprise-safe
2. avoid dead blank pages
3. explain whether a queue is empty, unavailable, or permission-restricted

Required state types:

1. loading
2. empty
3. restricted
4. error

Rule:

1. each state must explain what happened
2. empty does not mean error
3. restricted does not mean broken

## 5. Row Hierarchy Standard

The row model should stay consistent across queue types.

### 5.1 Primary row identity

Every row should expose:

1. document or task reference
2. customer or subject
3. one supporting line of context

### 5.2 Priority information

Each row should then expose the information that changes urgency:

1. status
2. due date or age
3. blocker or warning note
4. owner or assignee if relevant

### 5.3 Action model

Allowed row actions in the first wave:

1. open record
2. open linked record
3. call or follow-up action only when the source data already supports it

Disallowed in the first wave:

1. invented workflow actions not backed by ERP behavior
2. inline mutations that bypass native audit behavior

## 6. List Family Variants

Mini-Phase 3 should use the same shell with different row models.

### 6.1 Quotation operational list

Primary columns:

1. quotation
2. customer
3. valid till
4. workflow or action state
5. owner
6. next move

Signals:

1. expiring soon
2. awaiting approval
3. no follow-up recently

### 6.2 Sales-order operational list

Primary columns:

1. sales order
2. customer
3. delivery posture
4. billing posture
5. promised date
6. owner

Signals:

1. partially delivered
2. due soon
3. blocked by approval

### 6.3 Customer follow-up task list

Primary columns:

1. task
2. reference document
3. customer
4. due date
5. owner
6. reason

Signals:

1. overdue callbacks
2. today follow-up
3. stale no-response tasks

### 6.4 Invoice outstanding list

Primary columns:

1. sales invoice
2. customer
3. due date
4. outstanding value
5. settlement posture
6. linked sales context

Signals:

1. overdue
2. partially paid
3. credit or return impact

### 6.5 Return and exception list

Primary columns:

1. source document
2. return document
3. customer
4. stage
5. financial or fulfillment impact
6. owner

Signals:

1. unresolved return
2. billing mismatch
3. source document still open

### 6.6 Customer directory list

Implemented route:

1. `/desk/sales-console-worklist/customer-directory`

Primary columns:

1. customer
2. territory
3. customer group
4. outstanding exposure
5. credit posture

Controls:

1. territory
2. customer group
3. keyword

Signals:

1. visible customers
2. customers with outstanding exposure
3. customers with recent sales activity

### 6.7 Item directory list

Implemented route:

1. `/desk/sales-console-worklist/item-directory`

Primary columns:

1. item code
2. item name
3. item group
4. stock posture

Controls:

1. item group
2. availability
3. keyword

Signals:

1. visible items
2. in-stock items
3. out-of-stock items

## 7. Technical Foundation

Mini-Phase 2 established a shared runtime module and shared visual layer.

### 7.1 Runtime surface

Module:

1. `public/js/runtime/list_page/list_page_shell.js`

Namespace:

1. `window.erpWorkspaceUiListPage`

Purpose:

1. mount a reusable list shell into a target node
2. render summary, controls, signals, results, and state surfaces from one config object
3. bind shared toolbar and row actions through one event contract
4. render text and select filter controls from the backend contract
5. preserve active filters while refreshing a page

### 7.2 Shared CSS surface

Mini-Phase 2 uses runtime shell styles and the existing ERP UI visual system:

1. `public/js/runtime/list_page/list_page_shell.js`
2. `public/css/erp_workspace_ui.css`

Rule:

1. list pages must reuse the same surface tokens, border language, chip tones, and shadow depth already used by frozen pages
2. list pages should feel like part of the same product family

### 7.3 Config contract for later pages

The shared runtime is built around this page contract:

1. `summary`
2. `controls`
3. `metrics`
4. `results`
5. `state`
6. `onAction`

That means each future list page should mostly supply data and variant configuration, not rebuild layout primitives.

## 8. State Rules

### 8.1 Loading

Use skeleton table rows or a loading panel inside the results surface.

Do not:

1. flash native ERP list content first
2. show layout jumps before the shared shell mounts

### 8.2 Empty

Use truthful operational language.

Examples:

1. `No quotations currently need sales action.`
2. `No outstanding invoices match the active scope.`

### 8.3 Restricted

Use permission-safe language.

Example:

1. `This queue is outside your current role scope.`

### 8.4 Error

Explain that the queue did not load and keep a recovery action visible.

## 9. Current Consumption Rule

When adding or changing a Sales Console worklist, implementation should happen in this order:

1. add or update the backend builder in `sales_console/worklist.py`
2. keep the page route on `sales-console-worklist`
3. pass data through the shared list contract
4. use row action targets instead of custom per-page click logic
5. only add runtime behavior when it benefits more than one list page

## 10. Current Output Of Mini-Phase 2

Mini-Phase 2 is complete for the current Sales Console list family because:

1. the shared operational-list standard is written
2. the shared list-shell runtime exists in the ERP UI package
3. operational queues, approval queues, Customers, and Items are routed through the shared shell
4. the bare worklist route has an intentional guard state instead of silently rendering a misleading page
5. Customers and Items were manually checked in the live Desk UI on 2026-04-23
