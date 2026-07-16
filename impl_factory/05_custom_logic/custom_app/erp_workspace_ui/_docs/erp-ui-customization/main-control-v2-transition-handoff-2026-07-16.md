# Main Control V2 Transition Handoff

Date: 2026-07-16

Status: Source-only handoff package for a fresh Main Control task. It records the verified state after Finance Cycle 1 closure and defines the next planning outcome. It does not start Finance Cycle 2, select a capability, change runtime behavior, perform a live action, stage, commit, push, or run a protected gate.

## 1. Transition Decision

Create a fresh Main Control v2 task at the Finance Cycle 1 boundary. The current long-running Main Control task becomes a historical audit reference and should not remain the day-to-day controller.

The new controller must use repository state, accepted closure documents, installed source, and fresh validation as authority. The historical predecessor is the long-running Codex task that produced Finance Cycle 1 closure commit `aeed243c...` and this transition request; the Owner should pin or rename it `Main Control v1 - through Finance Cycle 1`. It may be consulted for chronology, Owner decisions, and browser evidence, but the new controller must not rely on conversational memory for current technical truth.

The first outcome under Main Control v2 is the Finance & Accounting Capability Map and Integration Plan. This is a planning map, not Finance Cycle 2. It must not implement or select the next capability.

## 2. Repository and Deployment Identity

### Source

- Repository: `/home/deploy/erp-projects/erpai_project1_erpnext_ui_design`
- App root: `/home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/05_custom_logic/custom_app/erp_workspace_ui`
- Branch: `feature/erpnext-ui-design`
- Verified parent baseline before this handoff candidate: `aeed243c76832c958a269d3ca2a0a58ce7616097`
- Upstream: `origin/feature/erpnext-ui-design`
- Canonical Git remote: `https://htayaung-data@github.com/htayaung-data/erpnext-ai-agent.git`
- Ahead/behind before this handoff candidate: `0/0`
- Git index at handoff: empty
- `git diff --check HEAD`: passed for tracked changes
- Explicit trailing-whitespace scans: passed for both untracked handoff documents
- Remote access: SSH to `deploy@152.42.253.113` with the existing project SSH credential; never copy a private credential into a task or document

The expected transition baseline is one documentation-only successor commit whose parent is `aeed243c...` and whose manifest is exactly the following three paths:

- `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/README.md`
- `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/codex-delivery-operating-model-v1-pilot-2026-07-16.md`
- `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/main-control-v2-transition-handoff-2026-07-16.md`

The actual successor hash cannot exist inside its own content. Capture it in the staging/commit/push receipt and provide it to Main Control v2. The new controller must verify the actual current HEAD, its parent, exact manifest, and upstream relationship rather than requiring HEAD to remain `aeed243c...`.

Before that commit, controlled staging must confirm exactly 3/3 paths, zero extras, hashes matching the final cold-reviewed snapshot, and `git diff --cached --check` passing. This explicitly covers the two currently untracked Markdown files that `git diff --check HEAD` cannot inspect.

### Live

- Repository: `/home/deploy/erp-projects/erpai_project1`
- App root: `/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/erp_workspace_ui`
- Live branch: `feature/ai-assistant`
- Live HEAD at handoff: `4db4a61976019e428c0744528817781be271b3c6`
- Live upstream: `origin/feature/ai-assistant`, matching at handoff
- Live Git index at handoff: empty
- Site: `erpai_prj1`
- Backend container: `erpai_project1-backend-1`
- Public host: `https://meet.erpbosai.com`
- Health at handoff: backend healthy; public ping returned `{"message":"pong"}`
- Live worktree: broadly dirty deployment/integration mirror; never use broad synchronization

### Installed Versions

- Frappe: 16.5.0
- ERPNext: 16.4.1
- HRMS: 16.4.0
- Frappe Assistant Core: 2.3.1
- ERP Workspace UI: 0.0.1
- AI Assistant UI: 0.0.1

Versions must be rechecked before any future source-proof or live task that depends on installed behavior.

### Point-in-Time Read-Only Transition Receipt

On 2026-07-16, Main Control re-verified the source HEAD/upstream relationship, seven-path dirty classification, empty source/live indexes, live HEAD/upstream relationship, installed versions, healthy backend/public ping, referenced closure/standard files, and all 19 source/live runtime hashes. No repository, service, cache, metadata, permission, migration, or live state was changed by that verification. These are dated reported facts, not permanent guarantees; the Owner ratifies their use by accepting this handoff, and Main Control v2 must revalidate every mutable fact before relying on it.

## 3. Known Source Exclusions

The following four paths are unrelated to the Finance closure and remain local, dirty, unstaged, and uncommitted. They must be excluded from every broad status conclusion and every future allowlist unless separately owned:

| Path | Status | Bytes | Current SHA-256 | Baseline/owner receipt |
| --- | --- | ---: | --- | --- |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py` | modified | 368090 | `01668e175610d9d090ea51018badbde8b021103afe13ed878782a58b8ce3b224` | HEAD hash `a36d7ad909c8fa0cb6d2b7237fb63f42df8dde79701b2688a3f9e79c9f9bfa9f`; AI stream, not Finance |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/browser_supplier_payables_fixture_diagnostic.py` | untracked | 11615 | `d9822184b26f3c1ebaf5b93663b1f6c3a495b6482f013092d955748dfdf963c5` | AI stream, not Finance |
| `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/ui_smoke/sales_final_acceptance_audit.js` | untracked | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | Sales stream/hygiene debt, not Finance |
| `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/a.out` | untracked | 416 | `0063411e61152850243132aa87ef12844a8724adb671bf4f38793bcd2b1ce339` | Generated artifact with unresolved owner; do not delete or stage |

During preparation of this source-only handoff, the worktree has exactly seven classified dirty paths: the four exclusions above plus `README.md` and the two new handoff documents. No path is staged. After a separately approved handoff commit, the expected dirty state returns to the four exclusions only. A status or hash change within an exclusion requires a refreshed owner receipt; any additional or unclassified path is a stop condition.

## 4. Finance Commit Chain

- `5231d078389568e2d6db552d1598f3bdc9aee082` - `feat(finance): add control desk AR posture`
- `50eec8ab26ea5d4eb587f63871d274d6bc139eec` - AR closure documentation
- `e198fa4aaca77c7ed2f65c98256644b20e7bbeb0` - AR hardening
- `391bf6bc7df862946a64882d1327d87600f27bc4` - `feat(finance): add payables count posture`
- `faa8e2ca2d869d38fc3d86d262ac737f84b642c6` - unavailable-copy hardening
- `0e18096377a628135668419d0c7aa72774f23030` - AP count closure documentation
- `6d519281464598a220db354d8f04a4441928dd6d` - Cycle 1 correctness, lifecycle, shared-runtime, and cross-workspace hardening
- `aeed243c76832c958a269d3ca2a0a58ce7616097` - `feat(finance): close cycle one workspace`

The final Finance closure artifact was drafted before the last commit and therefore names `6d519281...` as its then-current source HEAD. Current branch authority is `aeed243c...`, which contains that artifact and the final 18-path closure package.

## 5. Finance Cycle 1 Closure Truth

Primary closure artifact:

- `finance-accounting-phase-f6f-cycle1-final-validation-closure-readiness-2026-07-16.md`

Finance Cycle 1 is closed only for a bounded, company-scoped, read-only aggregate Finance Control Desk. This is not closure of the full Finance product.

### Accepted Route and Landing

- Route: `/desk/finance-control-desk`
- Page roles: Accounts Manager and Accounts User
- Root landing: Finance-authorized users who do not match a higher-precedence Sales or Procurement role land on Finance Control Desk
- Landing precedence remains: Sales > Procurement > Finance > Warehouse
- Finance search remains disabled

### Role Nuance

- Shell roles in the service include Accounts User, Accounts Manager, Auditor, and System Manager.
- Overview roles include Accounts User, Accounts Manager, and Auditor.
- Manager financial aggregates are Accounts Manager only.
- Page metadata grants Accounts Manager and Accounts User access; service role names do not automatically grant direct Page access to Auditor or System Manager.
- System Manager is not automatic Finance authority.

### Company and Currency

- Accepted deployed company: `Mingalar Mobile Distribution Co., Ltd.`
- Accepted deployed currency: MMK
- One permission-visible Company may use `single_company_site_fallback`.
- Multi-company ambiguity, malformed configuration, or permission uncertainty fails closed.
- This is deployment-specific acceptance, not proof of general multi-company readiness.

### Receivables Count Posture

- Source: Sales Invoice, permission-preserving and selected-company scoped.
- Output: identity-free aggregate current/not-overdue and overdue bucket counts.
- Manager-only display.
- Returns are excluded from the AR count population. Payment schedules, payment terms, future posting, invalid due dates, malformed results, wrong company, unsupported states, permission uncertainty, and other unproven complexity fail closed.
- `as_of_date` is explicit and current/not-overdue includes invoices due on or after the cutoff.

### Receivables Amount Posture

- Source: Payment Ledger Entry voucher-outstanding semantics, separate from the Sales Invoice count source.
- Output: manager-only aggregate MMK aging amounts as exact fixed-scale strings.
- Sales Invoice and Payment Ledger composite voucher sets reconcile exactly per bucket.
- Precision comes from ERPNext currency precision and approved System Settings rounding, not user defaults.
- Wrong company, currency disagreement, malformed identities, duplicate or uncorrelatable activity, future activity, submitted returns, permission uncertainty, count/amount population disagreement, and concurrent inconsistency suppress the complete amount posture.
- Low-population suppression remains conservative; no partial bucket or total survives failure.

### Payables Count Posture

- Source: Purchase Invoice, permission-preserving and selected-company scoped.
- Output: Accounts Manager-only aggregate count posture.
- Payment schedules or payment terms, advances, returns/debit notes, holds, missing due dates, future posting, unsupported status, malformed aggregate output, wrong company, permission failure, and unproven future selected-company Supplier Payment Ledger activity fail closed.
- AP counts may be conservatively unavailable when the broad future-ledger gate cannot prove as-of completeness.
- No AP amounts are approved.

### Browser and Payload Controls

- Exact raw payload contracts are validated before normalization, caching, or rendering.
- No row or identity payload is accepted.
- Stale financial DOM, cache, announcement, and focus authority clear immediately on refresh, invalidation, hide, timeout, failure, re-entry, or Page-body replacement.
- Request tokens prevent stale success or error responses from changing the current page.
- Finance mounts only in its supplied wrapper-owned Frappe `page.body`.
- The persistent polite live region is contained inside a Finance-owned positioned shell.
- Accepted desktop and mobile geometry has one effective Desk scroll range and no artificial blank tail.

### Explicitly Blocked

- Customer, supplier, invoice, voucher, account, Payment Ledger, GL, bank, or payment rows and identities.
- Drilldowns and native Finance reports or routes.
- Export, download, print, or report pass-through.
- Sales Invoice, Purchase Invoice, Payment Entry, Journal Entry, or GL lifecycle mutation.
- Posting, payment, reconciliation, write-off, tax, close, bank execution, email, notification, portal, or customer/supplier action.
- Payment Schedule aging or allocation semantics.
- AP amount posture.
- General Ledger, trial balance, financial statements, cash/bank, tax, close, consolidation, and cross-workspace accounting implementation.

### Accepted Evidence

- Focused Finance tests: 195 passed.
- Cross-workspace regression tests: 429 passed.
- Full unit discovery: 624 passed.
- Finance lifecycle smoke: passed.
- Pinned renderer smoke: passed at 1366px, 390px, and 320px.
- Authenticated Accounts Manager and Accounts User browser review: accepted.
- Authenticated Sales and Procurement browser checks: accepted.
- Warehouse route/isolation check: accepted.
- Source/live parity: 19 of 19 scoped runtime paths match.

### Accepted Residual Risks

- Concurrent accounting changes may make AR amounts temporarily unavailable.
- AR count/identity/amount reconciliation relies on one Frappe request transaction under MariaDB `REPEATABLE-READ`; no independent snapshot or locking mechanism was added. Recheck deployed isolation and request-transaction behavior before reusing the pattern.
- The conservative AP future-ledger gate may suppress counts unrelated to the candidate invoices.
- Authenticated screen-reader and forced-colors evidence is deferred.
- No protected gate was claimed for Finance Cycle 1.

## 6. Source/Live Runtime Parity Receipt

The following Cycle 1 runtime files were byte-identical between source and live at handoff:

| Runtime path under `erp_workspace_ui` | SHA-256 |
| --- | --- |
| `boot.py` | `9c8b422821586822825349484977a12b858631b4e876b14918a7ed37f0d62dae` |
| `workspace_registry.py` | `efaafaa2c7a95bf0efe67d019328c1ff8cdc45e03faaab4233adcbb468375822` |
| `workspace_governance_manifest.py` | `b8f582938ee9737484b60637e959248bdaa3e56298221084cf99c59d6342768f` |
| `public/js/runtime/console/workspace_registry.js` | `1196afd99234296e41671196bb357af546d1e04212dffbf0dc51bb8a78f144b6` |
| `public/js/runtime/console/workspace_console_sidebar.js` | `c8bbd2b7690c6c126d626556ba09892ebc92698420d35b49fc946caefc9ac674` |
| `public/js/erp_workspace_ui_boot.js` | `443e7df4e6dc3953b306010990bf03d98845b98f41f38615bc97080e0de2e6dc` |
| `public/js/procurement_console/procurement_console_page.js` | `95001b3ad95bdc53c0aaf78b05db3eb1089e7ef9814256ac9dbde36cca0e6f28` |
| `public/js/runtime/child_page/child_page_helpers.js` | `4e435ecf3c4367e4f15a2e2046b42ffe681eec068cbbfc28c4839e20a4de1c2b` |
| `public/js/runtime/child_page/child_page_operating_actions.js` | `1d591f4bca03f732e144b939fd0021ec0aad04b0e9a57aab9a48605e58054caa` |
| `erp_workspace_ui/erp_workspace_ui/page/finance_control_desk/finance_control_desk.js` | `52356627d4be4843c200c51a3b1bb11c070b5fdb4c51e2f26e5952ff94011e0c` |
| `erp_workspace_ui/erp_workspace_ui/page/sales_console/sales_console.js` | `2ae91711eb99ac0e1cdc2767a76a1435324bd55d9ed6e77786e87ddb5a7f0cbf` |
| `erp_workspace_ui/erp_workspace_ui/page/sales_console_worklist/sales_console_worklist.js` | `11eed6ab3e96d6c62ef742a8e31506e361f93367edb0618836f07a008272cfee` |
| `erp_workspace_ui/erp_workspace_ui/page/sales_console_report/sales_console_report.js` | `d983e06bce28900e4deeb330c4260d0d7066abdf0e26a068561a68284b3d14d6` |
| `erp_workspace_ui/erp_workspace_ui/page/procurement_console_worklist/procurement_console_worklist.js` | `2806077974dac131896f1a8cef1efd5e6bb188c60e36a40a8570950f18387407` |
| `erp_workspace_ui/erp_workspace_ui/page/procurement_console_report/procurement_console_report.js` | `318e991c28313ffbafe726872876ab221194eb59feecaffbf27ac7340e23173d` |
| `finance_accounting/service.py` | `f7a5aa8c82011b385cc0c5963575162ace51341477286c054fb9dbcc8290ecad` |
| `sales_console/service.py` | `dc2b05dcb008723b95cc1054e0ecdf8da97b095c1af44368a40d7f25f156db27` |
| `procurement_console/service.py` | `d730588927c309700dfa20c784fec284fceb6f2252b0711a5fb8a4b39ce74abb` |
| `warehouse_console/service.py` | `ed715c17683cc8a48d23b06781ad32d1d93d0abc4cd656c22adc80f4a092ae9f` |

These hashes are a handoff receipt, not permanent expectations. Recompute them before a future live operation.

## 7. Accepted and Protected Workspace Baselines

Sales and Procurement retain formally protected baselines. Warehouse W16H and Finance Cycle 1 are accepted closed-scope baselines that must be preserved from regression through the interim gates below; neither is claimed as formally `Protected` under the Frozen Workspace Protection Package Standard.

### 7.1 Sales Console

Authoritative references:

- Historical baseline: `sales-console-final-freeze-2026-05-03.md`
- Current protection package: `sales-console-frozen-protection-package-2026-05-09.md`
- Current v2 protection gate: `sales-console-freeze-v2-protection-gate.md`

The v2 package and gate supersede the v1-era baseline wherever they differ.

Preserve:

- Canonical Sales routes, role landing, worklists, reports, Customers, Items, and managed document flows.
- One-shell lifecycle, breadcrumbs, mobile behavior, governed search, AI/suggestion request isolation, and timer invalidation.
- Narrowly approved Sales native/managed document exceptions.
- Existing removal of the standalone Dashboard pattern.

Do not:

- Copy Sales AI, inquiry, queue taxonomy, pricing/stock context, or native-form enhancement into Finance.
- Broaden native targets or global dispatch.
- Change Sales landing priority while implementing Finance.
- Patch Sales incidentally in a Finance outcome.

Any shared UI or runtime change must run the Sales protection and regression gates.

### 7.2 Procurement Console

Authoritative later closure:

- `procurement-console-final-freeze-closure-2026-05-25.md`

Preserve:

- Purchase-role landing and productized Procurement routes.
- Managed Purchase Requisition, RFQ, Supplier Quotation, Purchase Order, detail, review, and follow-up boundaries.
- Quick Find preview before explicit Open.
- Preview/PDF restrictions and native-escape closure.
- Supplier and Buying Item productized information architecture.

Do not:

- Add raw native list/report/form escape as a convenience.
- Add send/email, receive, bill, pay, submit, cancel, amend, or broad Supplier/Item mutation.
- Copy Procurement queues, roles, supplier/item semantics, receipt visibility, or billing visibility into Finance.
- Treat the older registry label `phase_3` as proof that Procurement is not frozen; the later final closure is authoritative.

Ownership boundary: Warehouse currently owns the accepted custom receipt visibility and workflow-coordination surface only. ERPNext receipt execution ownership remains an unapproved later Warehouse decision. Finance invoice, payment, ledger, tax, and accounting authority also requires separately approved future capabilities.

### 7.3 Warehouse Console

Authoritative closure:

- `warehouse-console-phase-w16h-custom-workflow-closure-2026-07-04.md`

Preserve:

- Overview as navigation/status rather than an active-work dumping ground.
- Dedicated receiving, picking, returns, internal-transfer, and cycle-count custom routes where accepted.
- Bounded custom-record posture, custom search/recall, and controlled unsupported states.

Do not:

- Interpret custom workflow closure as ERP stock execution approval.
- Add Purchase Receipt, Delivery Note, Pick List, Stock Entry, Stock Reconciliation, stock ledger, balance, reservation, valuation, posting, notification, or accounting execution.
- Copy Warehouse custom writes, queue semantics, PO/SO/Bin/Stock reads, or operational actions into Finance.
- Treat the registry label `w8c_transfer_visibility` as the complete current roadmap; W16H is the later custom-workflow closure authority.

### 7.4 Finance Cycle 1

Finance Cycle 1 is an accepted closed-scope baseline for all future Finance and shared-runtime work. Preserve the bounded aggregate-only contract described in Section 5. The next map may classify future capabilities, but it must not expand Cycle 1 at runtime or claim a formal Finance protected gate.

## 8. Shared UI and Runtime Contract

Required references:

- `frozen-workspace-protection-package-standard-v1.md`
- `shared-core-workspace-adapter-contract-v2.md`
- `shared-component-and-implementation-golden-rule-standard-v1.md`
- `enterprise-shared-ui-component-standard-v1.md`
- `enterprise-shared-ui-component-implementation-contract-v1.md`
- `native-exception-policy-v1.md`
- `multi-workspace-foundation-contract-v1.md`
- `workspace_registry.py`
- `workspace_governance_manifest.py`
- `public/js/runtime/console/workspace_registry.js`
- `public/js/runtime/console/workspace_console_sidebar.js`
- `boot.py`

Follow these principles:

- Shared core owns lifecycle, teardown, one-shell behavior, sidebar/header/filter grammar, responsive foundations, target validation, request isolation, and common state rendering.
- Workspace adapters own roles, routes, domain payloads, business copy, source semantics, and approved actions.
- Backend and browser workspace identity must be registered consistently.
- Exactly one managed shell and one current sidebar item are allowed.
- Search and dispatch authority must be bound to workspace, route, target, query, request token, and generation.
- Route, input, clear, timeout, supersession, and departure must invalidate stale authority.
- Productized targets are preferred; native exceptions require explicit manifest classification and permission gating.

Do not:

- Copy a complete page controller from another workspace.
- Move domain logic into shared runtime.
- Add global overflow, height, or focus fixes for a workspace-local layout defect.
- Add global document/list/report dispatch helpers.
- Let stale requests cache, render, announce, or restore focus.
- Fix another workspace inside the current outcome without a separate impact decision.

The complete shared-core trigger set is the set defined by the Frozen Workspace Protection Package Standard. It includes `hooks.py`, app boot JavaScript, backend/browser registries, governance manifests, shared CSS, sidebar/search, list/report/child runtimes, route/page lifecycle, native-exception policy, and shared-component/adapter contract documents. A triggered change is product-wide and requires the formal Sales and Procurement gates plus the interim Warehouse and Finance gates.

Until Warehouse has a dedicated executable protection gate, its interim source gate is the full Warehouse regression suite, registry/governance tests, governed route/search/active-item checks, and any applicable custom-workflow smoke. A live shared-runtime change additionally requires exact source/live parity and authenticated Warehouse Manager navigation/isolation acceptance.

Until Finance has a dedicated executable protection gate, its interim documentation gate is exact-manifest validation, documentation reference/whitespace/overclaim checks, and proof that no runtime path changed. Its interim runtime source gate is the full Finance test suite, Finance lifecycle smoke, pinned renderer smoke at 1366px/390px/320px, and cross-workspace regression tests. A live shared-runtime change additionally requires exact source/live parity, role diagnostics, and authenticated Accounts Manager/Accounts User browser acceptance.

## 9. Known Traceability Debt

The following labels lag behind later accepted closures:

- Finance registry may still report `cycle_1_f6_quality_gate_pending` although commit `aeed243c...` and F6F Owner evidence close Cycle 1.
- Procurement registry may still report `phase_3` although the later final freeze closure is authoritative.
- Warehouse registry may still report `w8c_transfer_visibility` although W16H later closes the custom workflow package.
- Sales machine markers may retain v1-era values while the v2 protection package is the later protection authority.
- Final post-push Owner acceptance exists in the historical predecessor task, but there is no separate post-push Owner-acceptance document beyond F6F closure prose and the `aeed243c...` history.

These are planning-map traceability findings. Do not patch them opportunistically during capability mapping. Record them, assess their governance impact, and propose a separate controlled correction only if needed.

## 10. Next Outcome: Finance Capability Map and Integration Plan

This outcome is Level 0 enterprise coverage plus Level 1 detail for up to three conditional candidates. It is not Cycle 2 and must not choose the winner.

### 10.1 Required Capability Families

1. Legal entity, company, chart of accounts, currency, precision, fiscal period, opening balance, and master-data quality foundations.
2. Record-to-Report: GL, journals, trial balance, financial statements, reconciliation, period close, audit trail, accruals, provisions, prepayments, reversals, FX revaluation, deferred revenue/expense, automated or background GL-producing processes, and Finance Books/multi-book accounting.
3. Order-to-Cash: AR, collections, credit, expected-credit-loss or bad-debt policy, write-offs, revenue, receipts, and customer accounting integration.
4. Procure-to-Pay: AP, supplier and employee expenses, expense claims, invoice controls, approvals, payments, and supplier accounting integration.
5. Treasury: cash, bank, liquidity, bank reconciliation, cash forecasting, and payment authority.
6. Financing and capital: debt, interest, investments, equity, dividends, leases, and related measurement/disclosure needs.
7. Tax and localization: indirect tax, withholding, filings, statutory reports, and local requirements.
8. Dimensions, budgets, cost centers, projects, and management accounting.
9. Fixed assets and depreciation.
10. Inventory valuation, COGS, landed cost, and manufacturing accounting.
11. Intercompany, consolidation, eliminations, and group reporting.
12. Controls: segregation of duties, approvals, audit, retention, recovery, migration, observability, data-quality monitoring, payroll/employee accounting, and autonomous-posting controls for schedulers, background jobs, deferred accounting, revaluation, depreciation, and other GL-producing processes.
13. Cross-workspace accounting review surfaces and custom request/handoff contracts.

The map must reconcile every installed ERPNext accounting capability and every category in an independent enterprise Finance taxonomy to exactly one status: included, deferred, not applicable, or unknown. Every deferred/not-applicable classification needs a reason and Owner confirmation; no discovered capability may remain unmapped.

### 10.2 Required Fields Per Capability

- Business purpose and decisions enabled.
- Primary users and authority roles.
- Requirement classification: now, later, conditional, or not applicable.
- ERPNext source of truth and lineage.
- Visibility, review, approval, and execution boundary.
- Dependencies and prerequisites.
- Integration with Sales, Procurement, Warehouse, HR, and external systems.
- Classification: native reuse, custom facade, custom workflow, integration, or defer.
- Confidence: proven, partial, or unproven.
- Nonfunctional needs: performance, audit, security, resilience, retention, and accessibility.
- Main risks and required proof.

### 10.3 Business Fact Sheet

Separate known facts from Owner decisions and unknowns. At minimum confirm:

- Legal entities and future multi-company needs.
- Base and transaction currencies.
- Fiscal calendars and closing policy.
- Chart of accounts ownership and dimensional reporting.
- Tax jurisdictions and statutory obligations.
- Banking, payment, approval, and signing authority.
- AP/AR volumes, payment schedules, credit/collection policy, and aging expectations.
- Inventory, landed cost, valuation, and manufacturing needs.
- Fixed assets, budgets, projects, intercompany, and consolidation needs.
- Audit, retention, recovery, migration, and integration obligations.

Do not silently convert unknowns into design assumptions.

### 10.4 Integration Contract Template

For each cross-domain flow record:

- Producer and authoritative source.
- Consumer and business owner.
- Permitted and blocked data.
- Direction and trigger.
- Consistency and freshness expectation.
- Idempotency and duplicate handling.
- Reconciliation method and control total.
- Failure owner and stale/unavailable behavior.
- Audit and retention evidence.
- Permission and segregation-of-duties boundary.
- Prerequisites and rollback/recovery.

### 10.5 Conditional Candidate Matrix

Score candidate work scopes using documented weights for:

- Business urgency.
- Accounting/control risk reduction.
- Data readiness and source confidence.
- Dependency centrality.
- Cross-workspace leverage.
- Implementation and operational cost.
- Time to safe value.
- Execution, regulatory, and migration risk.

The map may recommend a conditional ordering under explicit assumptions. The Owner selects the first Cycle 2 outcome in a later decision.

### 10.6 Required Deliverables

- Enterprise Finance capability map.
- Installed-ERPNext and enterprise-taxonomy coverage reconciliation with included/deferred/not-applicable/unknown status for every discovered capability.
- Known/unknown business fact sheet.
- Current-state source and control inventory.
- Cross-workspace integration plan.
- Dependency graph and critical prerequisites.
- Risk, control, and segregation-of-duties register.
- Native/custom/integration/defer classification matrix.
- Up to three Level 1 candidate briefs.
- Conditional prioritization matrix.
- Accepted/protected workspace impact matrix.
- Completed evidence scorecard with evidence references, `N/A` reasons, and independent confirmation.
- Validation receipt distinguishing source, staging, live, browser, commit, push, and closure states.
- Decision log and unresolved Owner questions.
- Proposed Cycle 2 selection gate, without selecting the winner.

## 11. Recommended Main Control V2 Execution

Use the Codex Delivery Operating Model V1 Pilot.

1. Re-verify source HEAD, upstream, dirty paths, installed versions, MariaDB isolation/request-transaction behavior, and the 19-path parity receipt.
2. Freeze a docs-only capability-map charter.
3. Allocate independent read-only tracks for ERPNext finance semantics, business capability coverage, integration/accepted-protected workspaces, and controls/release evidence.
4. Use `gpt-5.6-sol` at xhigh or max for Main Control synthesis and the final accounting/security review.
5. Use `gpt-5.6-terra` only for bounded inventory and reference indexing where outputs are directly verifiable. If an exact model is unavailable, record the strongest-available frontier substitute.
6. Keep one writer for the map artifacts.
7. Use installed ERPNext source and official ERPNext documentation as primary product authority. Use at most two external ERP pattern references for gap comparison; they must not override installed behavior or be copied as design.
8. Reconcile reviewer conflicts explicitly.
9. Stop on any unclassified path, unproven financial claim, protected-workspace regression, or scope expansion.
10. End with a planning recommendation and Owner decision request. Do not implement Cycle 2.

## 12. New Main Control Bootstrap Checklist

Before analysis begins, the new controller must report:

- Actual source HEAD, its relationship to parent baseline `aeed243c...`, exact transition manifest, and upstream equality.
- Exact dirty/excluded paths.
- Installed version confirmation.
- MariaDB `REPEATABLE-READ` and one-request transaction assumption confirmation before any AR source-pattern reuse.
- Finance Cycle 1 closure artifact and final commit confirmation.
- Formal Sales/Procurement protection references plus accepted Warehouse W16H and Finance Cycle 1 closure/interim-gate references loaded.
- Shared UI/runtime standards loaded.
- No runtime, staging, live, or protected-gate action authorized.
- Capability-map charter and reviewer allocation.

If any mutable baseline fact differs from the actual transition receipt, stop and reconcile before proceeding. The expected successor commit hash is supplied by that receipt; it is not required to equal the pre-handoff parent `aeed243c...`.

## 13. Bootstrap Prompt

Use `gpt-5.6-sol` with xhigh or max reasoning, or the strongest available frontier substitute with the substitution recorded.

You are Main Control v2 for the ERP Workspace UI program. Read and treat `main-control-v2-transition-handoff-2026-07-16.md` and `codex-delivery-operating-model-v1-pilot-2026-07-16.md` as the transition charter, then independently verify every mutable baseline fact against the repository and deployed environment before relying on it. Access the host as `deploy@152.42.253.113` using the existing project SSH credential; never expose credential material. Verify the actual transition commit receipt, its `aeed243c...` parent, exact three-path manifest, and upstream state.

Your first outcome is the Finance & Accounting Capability Map and Integration Plan. This is not Finance Cycle 2, does not select the next capability, and authorizes no runtime change, live alignment, metadata or permission change, migration, staging, commit, push, protected gate, or accounting execution.

Use one writer and bounded independent read-only reviewers. Cover enterprise Finance capabilities, ERPNext source truth, known and unknown business facts, integration contracts, dependencies, segregation of duties, accepted/protected workspace impact, native/custom/integration/defer classification, and conditional prioritization. Produce Level 0 coverage for the complete Finance domain and Level 1 detail for no more than three conditional candidates. Use installed ERPNext source and official documentation as primary evidence.

Treat Sales and Procurement as formally protected baselines. Treat Warehouse W16H and Finance Cycle 1 as accepted closed-scope baselines governed by the documented interim gates, not as formally Protected packages. Follow the shared core/adapter and shared UI standards. Do not copy domain semantics between workspaces, broaden native targets, change landing priority, or modify shared runtime during this map. Record stale registry labels as traceability debt rather than patching them.

Start by reporting baseline verification, exact scope, exclusions, reviewer plan, and stop conditions. Finish with documents, independent review findings, residual unknowns, and an Owner decision request. Do not start implementation.

## 14. Transition Completion Rule

The current Main Control task may be archived after:

1. These handoff documents are accepted and committed under a separate approval.
2. A fresh Main Control v2 task reports successful baseline verification.
3. The Owner confirms that the new task is the active controller.

Until then, the current task remains available only to resolve handoff inconsistencies. It should not start new Finance implementation.
