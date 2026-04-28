# Sales Console Mini-Phase 6 Operating Foundation

Status: Slice 1 audit complete, Slice 2 contract baseline written, Slice 3 implemented, Slice 4 implemented, Slice 5 implemented, Slice 6 technical validation complete
Date: 2026-04-23
Source of truth: `page/sales_console/sales_console.js`, `page/sales_console_worklist/sales_console_worklist.js`, `page/sales_console_report/sales_console_report.js`, `sales_console/service.py`, `sales_console/worklist.py`, `public/js/runtime/list_page/list_page_shell.js`, `public/js/runtime/report_page/report_page_shell.js`, `public/js/runtime/child_page/child_page_shell_content.js`, `public/js/runtime/child_page/child_page_sidebar.js`, `public/js/runtime/child_page/child_page_support.js`, `public/js/quotation_form.js`, and `public/js/sales_order_form.js`

## 1. Purpose

This mini-phase exists to standardize how Sales Console behaves as one enterprise working surface before more workspace expansion begins.

It should answer these questions clearly:

1. where navigation should live
2. where page actions should live
3. which actions stay native ERPNext
4. which actions become productized Sales Console behavior
5. how drafts, worklists, reports, and the console home should feel like one system

This is not a cosmetic pass.

It is an operating-contract pass.

## 2. Core Decision

Mini-Phase 6 should be implemented in slices, not in one large mixed change.

The current UI already has good shared shells:

1. `erpWorkspaceConsoleRuntime` for console home behavior
2. `erpWorkspaceUiListPage` for worklists
3. `erpWorkspaceUiReportPage` for report-family pages
4. `erpWorkspaceUiChildPage` for Quotation and Sales Order execution pages

What is still incomplete is the shared operating contract across those shells.

Therefore the next correct move is:

1. audit the current truth first
2. define the operating contract second
3. standardize navigation and actions through shared layers
4. validate and freeze before starting another workspace implementation

## 3. Scope

Mini-Phase 6 covers:

1. Sales Console home
2. Sales Console worklists
3. Sales Console report-family pages currently present in the ERP UI branch
4. New Quotation
5. New Sales Order
6. shared navigation helpers
7. shared action posture
8. save, submit, print, email, assign, comment, share, and back-to-console behavior

Mini-Phase 6 does not cover:

1. shared stock availability implementation
2. a new workspace rollout
3. broad AI feature expansion
4. cosmetic spacing churn unless required by the operating contract

## 4. Slice Structure

Mini-Phase 6 should run in this order:

1. `MP6-S1` Current Truth Audit
2. `MP6-S2` Operating Contract Design
3. `MP6-S3` Shared Navigation Foundation
4. `MP6-S4` Draft Action Foundation
5. `MP6-S5` Worklist And Report Action Consistency
6. `MP6-S6` Validation And Freeze

## 5. Slice 1 Current Truth Audit

This section records the actual operating behavior visible in code on 2026-04-23.

### 5.1 Sales Console Home

Current truth:

1. home quick actions are productized in-page actions, not native module shortcuts
2. the current quick-action contract is:
   - `New Quotation`
   - `New Sales Order`
   - `Customers`
   - `Items`
3. action ordering and section ordering are role-aware through `ui_profile.action_order` and `ui_profile.section_order` in `sales_console/service.py`
4. navigation is resolved through target kinds such as `new_doc`, `list`, `report`, `report_page`, and `worklist`
5. route helpers already exist for:
   - native ERP lists
   - native query reports
   - productized Sales Console worklists
   - productized Sales Console reports
6. the only explicit sidebar customization on the home page today is the `Guideline` button injected into the Frappe sidebar

Implication:

1. the home page already behaves like a productized console
2. the left-side menu model is still partial, not a full cross-page navigation contract

### 5.2 Sales Console Worklists

Current truth:

1. worklists run through the shared `erpWorkspaceUiListPage` shell
2. the worklist controller already supports:
   - `refresh`
   - `back_to_console`
   - `apply_filters`
   - `reset_filters`
   - row actions routed through `action_targets`
3. Customers and Items are now productized worklists, not raw `List/Customer` or `List/Item` shortcuts
4. bare `/desk/sales-console-worklist` intentionally shows a guard state when no queue key is supplied
5. the shared list shell already supports toolbar actions, row actions, result states, and filter controls

Implication:

1. worklists already have a stronger in-shell action contract than the draft pages
2. they still do not share a fuller left-side workspace navigation model

### 5.3 Sales Console Report Family

Current truth:

1. the current ERP UI branch includes a productized report page controller and shared report runtime
2. the report page controller already supports:
   - `refresh`
   - `back_to_console`
   - filter submit
   - filter reset
   - action routing through `action_targets`
3. bare `/desk/sales-console-report` also guards when no report key is supplied
4. report pages are already following the same route-key pattern used by worklists

Implication:

1. the report family is close to the worklist operating pattern
2. it should be normalized into the same Mini-Phase 6 action contract instead of drifting separately

### 5.4 New Quotation Draft

Current truth:

1. New Quotation uses the shared child-page shell and shared draft-readiness rendering
2. the draft shell explicitly renders with `actions: []`
3. the page support copy explicitly says:
   - use the standard toolbar to save, submit, or route approval
4. workflow readonly treatment also tells the user to continue from the toolbar
5. print is represented as configuration inside the support/detail family, not as a shell-level operating action
6. comments and activity are surfaced through the shared support/footer layer
7. once saved, the page gains child-shell actions for related-record navigation and follow-up work

Implication:

1. draft guidance is productized
2. draft operating actions are still delegated to native ERPNext toolbar behavior
3. the shared child shell can render actions, but the draft posture intentionally leaves that band empty today

### 5.5 New Sales Order Draft

Current truth:

1. New Sales Order follows the same shared draft shell pattern as New Quotation
2. the draft shell also renders with `actions: []`
3. support copy explicitly says:
   - use the standard toolbar to save, submit, or route approval
4. workflow readonly treatment also points users back to the toolbar
5. print is configured inside the page support/detail system rather than a shell-level operating contract
6. comments and activity are surfaced through the shared support/footer layer
7. once saved, the page uses child-shell actions for linked deliveries, invoices, returns, customer, and follow-up work

Implication:

1. Sales Order and Quotation are architecturally aligned
2. both still rely on the native toolbar for core document operations

### 5.6 Saved Quotation And Sales Order Pages

Current truth:

1. both pages already have an `actionConfig(...)` layer
2. those shell actions are mostly downstream navigation and follow-up actions, not document-operation actions
3. current examples include:
   - open linked records
   - open customer
   - review or create follow-up tasks
   - open source quotation or downstream sales records

Implication:

1. a partial action model already exists for saved documents
2. it is not yet the same taxonomy used by Sales Console home, worklists, or reports

## 6. Gaps This Mini-Phase Must Close

The current audit shows these operating gaps:

1. there is no written shared action taxonomy across console home, worklists, reports, and draft pages
2. there is no fully standardized left-side Sales Console navigation model across all surfaces
3. `Back to Sales Console` exists on worklists and reports, but not as a standard draft-page operating action
4. save, submit, print, email, assign, comment, and share are not yet surfaced through one deliberate product contract
5. native ERPNext toolbar dependence is currently implied by copy, not governed by a written rule
6. collaboration actions still live mainly in native footer, timeline, or sidebar behavior
7. the child-page action band exists, but draft pages intentionally do not use it for operating actions yet
8. worklist and report shells are closer to the target contract than the draft pages, which creates cross-surface drift

## 7. Mini-Phase 6 Design Rules

Implementation must follow these rules:

1. preserve native ERPNext transaction truth for save, submit, print, and email
2. productize location, naming, and discoverability before inventing replacement behavior
3. do not bypass native audit or workflow behavior with custom mutations
4. keep Quotation and Sales Order aligned through shared runtime patterns
5. treat collaboration actions as a governed utility layer, not ad hoc page-local buttons
6. keep route guards explicit and user-safe
7. solve repeated issues in shared runtime first, not page by page

## 8. Slice Deliverables

### 8.1 `MP6-S2` Operating Contract Design

This slice should define:

1. the shared action taxonomy
2. the shared navigation taxonomy
3. native-vs-productized boundary rules
4. standard placement for save, submit, print, email, assign, comment, share, and back-to-console
5. which surfaces should own those controls

### 8.2 `MP6-S3` Shared Navigation Foundation

This slice should standardize:

1. the Sales Console left-side navigation model
2. console-home to worklist/report transitions
3. cross-page back navigation behavior
4. route guard and fallback behavior

### 8.3 `MP6-S4` Draft Action Foundation

This slice should standardize:

1. draft action posture for New Quotation and New Sales Order
2. how users discover save, submit, print, email, and collaboration actions
3. how the child-page shell should expose productized operating actions without replacing native truth

### 8.4 `MP6-S5` Worklist And Report Action Consistency

This slice should align:

1. worklist toolbar behavior
2. report toolbar behavior
3. row and state actions
4. back-to-console behavior
5. control reset and refresh posture

### 8.5 `MP6-S6` Validation And Freeze

This slice should prove:

1. routes are predictable
2. actions are discoverable
3. drafts, worklists, and reports now feel like one operating family
4. docs can be promoted into the later Golden SOP without guesswork
5. automated validation and browser smoke both support the freeze recommendation

## 9. Slice 2 Operating Contract Baseline

This section records the target contract Mini-Phase 6 should implement.

### 9.1 Shared Action Taxonomy

Mini-Phase 6 should use one semantic action model across all Sales Console surfaces.

Semantic action families:

1. `commit`
   - create a new record
   - save a draft
   - submit when workflow and permissions allow
2. `navigate`
   - move to console home
   - open a worklist
   - open a report
   - open a linked record
3. `communicate`
   - print
   - email
4. `collaborate`
   - assign
   - comment
   - share
5. `utility`
   - refresh
   - apply filters
   - reset filters
   - open native fallback when needed
   - open workspace guidance

Visual tiers:

1. `primary`
   - the main next-step action for the current surface
2. `secondary`
   - valid related actions that should stay visible
3. `utility`
   - lower-emphasis controls and collaboration actions

Rule:

1. semantic family and visual tier are different things
2. the same semantic family can appear in different tiers depending on surface context

### 9.2 Shared Navigation Taxonomy

Mini-Phase 6 should standardize these navigation states:

1. `workspace_home`
   - `/desk/sales-console`
2. `workspace_worklist`
   - `/desk/sales-console-worklist/<queue-key>`
3. `workspace_report`
   - `/desk/sales-console-report/<report-key>`
4. `draft_create`
   - `new Quotation`
   - `new Sales Order`
5. `document_execution`
   - saved Quotation
   - saved Sales Order
6. `native_fallback`
   - native ERP list, form, or query report when the productized route is not the right target

Rule:

1. left-side workspace navigation should derive from existing backend `ui_profile` ordering and `navigation` targets where possible
2. Mini-Phase 6 should not introduce a second hardcoded navigation registry if the backend already owns ordering truth

### 9.3 Native Versus Productized Boundary

Native ERPNext should remain authoritative for:

1. save
2. submit
3. workflow permissions
4. print generation
5. email sending
6. assignment and sharing permissions
7. audit trail and document status truth

The Sales Console product layer should own:

1. where those actions are surfaced
2. when they are shown, hidden, or disabled
3. labels and short explanatory notes
4. back-to-console behavior
5. cross-surface consistency
6. route fallback and guidance states

Rule:

1. Mini-Phase 6 may orchestrate native actions
2. it should not replace native transaction truth with custom mutations

### 9.4 Surface Contract By Page Type

#### Sales Console Home

Home should remain the primary workspace entry surface.

Required posture:

1. primary actions stay document-creation actions
2. secondary actions stay directory and workspace entry actions
3. left-side navigation should expose workspace destinations, not only the `Guideline` button
4. role-aware ordering should continue to come from `ui_profile`

#### Worklists

Worklists should use the list shell as the operating surface.

Required posture:

1. `Back to Sales Console` stays a standard top-level action
2. `Refresh`, `Apply`, and `Reset` stay utility actions
3. row actions stay minimal and truthful
4. no worklist should invent inline document mutations in this mini-phase

#### Reports

Reports should follow the same top-level operating contract as worklists.

Required posture:

1. `Back to Sales Console` stays standard
2. `Refresh` and filter reset/apply stay utility actions
3. report actions should use the same target-routing posture used by worklists
4. report controls must not drift into a separate product language

#### Draft Pages

Draft pages are the most important normalization target.

Required posture:

1. the child-page shell action band should become the standard operating band
2. `Save Draft` should be the primary commit action
3. `Submit` should only appear when the document is in a valid saved state and workflow allows it
4. `Back to Sales Console` should become a standard secondary navigation action
5. `Print`, `Email`, `Assign`, `Comment`, and `Share` should follow clear visibility rules instead of being discoverable only through native toolbar hunting
6. for unsaved drafts, unavailable actions should either stay hidden or explain why they are unavailable

#### Saved Execution Pages

Saved Quotation and Sales Order pages should keep linked-record and follow-up actions, but they should join the same broader action grammar.

Required posture:

1. linked-record navigation remains valid
2. communication and collaboration actions should follow the same naming and placement rules as draft pages
3. page-specific action clusters should not drift away from the shared child-shell contract

### 9.5 Reuse Rule For Implementation

Mini-Phase 6 should reuse existing shared infrastructure instead of adding new local systems.

Implementation rule:

1. use `sales_console/service.py` `navigation` and `ui_profile` as the source for workspace ordering where possible
2. use `erpWorkspaceUiListPage` for worklist action structure
3. use `erpWorkspaceUiReportPage` for report action structure
4. use `erpWorkspaceUiChildPage` action-band rendering for Quotation and Sales Order
5. do not add separate page-local action registries unless a shared contract cannot express the requirement

### 9.6 Collaboration Posture

Mini-Phase 6 should treat collaboration as a governed utility layer.

First-wave rule:

1. do not build a custom collaboration subsystem
2. use productized entry points into existing native comment, assignment, share, and activity surfaces
3. make those entry points discoverable and consistent across Quotation and Sales Order

## 10. Immediate Next Step

`MP6-S6` is now in validation status.

The remaining work is a short browser smoke on the live managed routes.

Once that smoke passes, Mini-Phase 6 can be treated as complete and ready for Golden SOP promotion.

## 11. Slice 3 Implementation Truth

Mini-Phase 6 now includes a shared navigation foundation.

Implemented pieces:

1. lightweight backend sidebar context method:
   - `get_sales_console_sidebar_context`
2. shared sidebar model built from:
   - `ui_profile`
   - `navigation`
   - `reports_catalog`
3. shared sidebar runtime:
   - `public/js/runtime/console/workspace_console_sidebar.js`
4. home-page bootstrap seeding so the sidebar can reuse existing Sales Console payload when available
5. automatic managed-route behavior for:
   - Sales Console home
   - Sales Console worklists
   - Sales Console reports
   - Quotation form
   - Sales Order form

Current behavior after `MP6-S3`:

1. a shared Sales Console sidebar navigation now mounts across managed routes
2. the sidebar removes itself when the user leaves managed Sales Console surfaces
3. the sidebar uses one role-aware section model instead of page-local sidebar item injection
4. the home page still keeps its separate `Guideline` button on Sales Console home only
5. Quotation and Sales Order drafts now inherit the same global Sales Console workspace navigation even though their core commit actions still depend on the native toolbar

That slice should convert this contract into a shared navigation foundation before draft-page action work begins.

## 12. Slice 4 Implementation Truth

Mini-Phase 6 now includes a shared draft and execution action foundation for Quotation and Sales Order.

Implemented pieces:

1. shared operating-action runtime:
   - `public/js/runtime/child_page/child_page_operating_actions.js`
2. shared action rules for:
   - `Save Draft`
   - `Submit` when native submit rules allow
   - `Back to Sales Console`
   - `Print`
   - `Email`
   - `Assign`
   - `Comment`
   - `Share`
3. Quotation and Sales Order shell wiring now consumes the shared operating-action layer
4. saved draft pages now keep commit actions visually primary while linked-record actions remain available as secondary follow-through actions
5. Quotation draft guidance copy now references the action band instead of the native toolbar

Current behavior after `MP6-S4`:

1. New Quotation and New Sales Order drafts now render a real operating action band instead of `actions: []`
2. native ERP transaction truth still owns save, submit, print, email, assignment, and sharing
3. unsaved drafts expose disabled communication and collaboration actions only when the user can use them later, with explicit reasons such as `Save draft first`
4. saved Quotation and Sales Order pages now inherit the same communication, collaboration, and back-to-console grammar alongside their existing linked-record actions
5. draft-state submit posture follows native Frappe rules:
   - submit appears only after save
   - submit stays hidden when workflow owns the transition
   - print respects native print-availability rules

## 13. Slice 5 Implementation Truth

Mini-Phase 6 now aligns worklists and reports with the same operating contract used by Sales Console drafts.

Implemented pieces:

1. worklist payload normalization now injects standard operating actions:
   - `Back to Sales Console`
   - `Refresh`
   - `Reset` and `Apply` when filter fields exist
2. report payload normalization now injects standard top-level actions:
   - `Back to Sales Console`
   - `Refresh`
3. report shell controls now render top-level toolbar actions alongside the existing report filter form
4. worklist controller fallback resolution now accepts shared non-row action targets, which supports native fallback actions cleanly
5. restricted worklists now expose `Open Native List` as a governed fallback when the user cannot operate the productized queue

Current behavior after `MP6-S5`:

1. worklists and reports now share the same top-level workspace grammar:
   - back to workspace
   - refresh current surface
   - apply and reset filters only where filters exist
2. report pages no longer depend only on form submit/reset for discoverable control actions
3. route-unavailable and restricted states now stay closer to the native-vs-productized boundary defined in Mini-Phase 6
4. worklist and report pages now feel structurally closer to the Quotation and Sales Order operating band, even though the visual shell remains appropriate to list/report surfaces

## 14. Slice 6 Validation Truth

Technical validation completed on 2026-04-23.

Automated evidence:

1. `node --check` passed for:
   - `public/js/runtime/report_page/report_page_shell.js`
   - `page/sales_console_worklist/sales_console_worklist.js`
   - `page/sales_console_report/sales_console_report.js`
2. `python3 -m py_compile` passed for:
   - `sales_console/worklist.py`
   - `sales_console/report.py`
3. unit tests passed:
   - `erp_workspace_ui.tests.test_sales_console_service_contracts`
   - `erp_workspace_ui.tests.test_sales_console_operating_contracts`
4. combined test result:
   - `Ran 14 tests ... OK`
5. `git diff --check` passed after the Slice 5 and Slice 6 updates

Validation conclusion:

1. the shared worklist/report operating contract is technically stable
2. the draft action band contract remains aligned with Quotation and Sales Order runtime
3. Mini-Phase 6 is ready for a short live browser smoke before it is treated as fully frozen for Golden SOP promotion

Required browser smoke before final freeze sign-off:

1. `/desk/sales-console`
   - confirm the shared Sales Console sidebar renders and the main destinations navigate correctly
2. `/desk/sales-console-worklist/customer-directory`
   - confirm `Back to Sales Console` and `Refresh` render
   - confirm filter actions still behave correctly
3. `/desk/sales-console-worklist/item-directory`
   - confirm the same worklist contract as Customers
4. `/desk/sales-console-report/sales-order-analysis`
   - confirm report toolbar actions render and remain usable
5. `/desk/sales-console-worklist`
   - confirm the route-guard state still reads correctly and exposes safe recovery actions
6. `new Quotation` and `new Sales Order`
   - confirm the operating action band renders correctly for draft state

Freeze recommendation:

1. after the browser smoke passes, Mini-Phase 6 can be treated as complete
2. the next program move should be shared stock availability for New Quotation and New Sales Order
