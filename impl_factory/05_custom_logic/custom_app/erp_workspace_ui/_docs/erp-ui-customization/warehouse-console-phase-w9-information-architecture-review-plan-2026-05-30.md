# Warehouse Console Phase W9 Information Architecture Review Plan

Date: 2026-05-30

Branch: `feature/erpnext-ui-design`

Status: docs-only W9 design and sequencing plan. This document does not implement Warehouse runtime, routes, APIs, tests, smokes, package scripts, or live alignment.

Runtime baseline before W9 design:

- W8A movement visibility runtime: `c408b85b9f9bdab9ac66e0be375930e50a8bece3`
- W8B movement review runtime: `fb337a26d75af22d130fcb0bf43b779794bde055`
- W8B smoke hardening: `20f6fbf3dc0c333f0e2381750f51ace8e0be8ecc`
- W8B protected baseline documentation: `5d225062b6c06d00fc64013e82eb35c18fc41576`
- W8B live smoke: `/tmp/warehouse-phase-w8b-live-smokefix3-20260530T023440Z/warehouse-w8b-movement-review-20260530T023444Z/warehouse-w8b-movement-review-summary.json`
- W8B protected live gate: `/tmp/warehouse-phase-w8b-protected-live-20260530T023604Z/protected-workspace-gate-summary.json`

## 1. Executive Recommendation

W9 should be a Warehouse information-architecture and cockpit polish phase before adding another operational route.

Recommended next implementation after this plan is accepted: W9A Warehouse Cockpit IA Polish.

W9A should not add new stock workflows. It should reorganize the existing Warehouse Overview and navigation around three operational pillars:

- **Work To Do**: inbound receiving and outbound picking.
- **Risks To Resolve**: stock exceptions and stock posture review entry points.
- **Movement To Understand**: movement visibility and movement review entry points.

The goal is a premium Warehouse cockpit that makes the current protected routes easier to understand, reduces duplicated cards, clarifies where to start, and keeps the user inside custom Warehouse pages. W9A should improve wayfinding and visual hierarchy, not expand stock execution capability.

W8C Transfer Visibility should wait until after W9A unless the owner explicitly prioritizes transfer posture over cockpit clarity. Transfer visibility is closer to Stock Entry execution and should not be added on top of an already dense Overview.

## 2. Research Basis

### 2.1 Current Protected Warehouse Baseline Reviewed

Current source and protected docs reviewed before writing this plan:

- W3/W3A read-only foundation and landing baseline.
- W4A Inbound Receiving baseline.
- W4B Receiving Review baseline.
- W5A/W5B Outbound Picking and Picking Review baselines.
- W6A/W6B Stock Exceptions and Stock Exception Review baselines.
- W7A Stock Posture Review baseline.
- W8A Movement Visibility baseline.
- W8B Movement Review baseline.
- `erp_workspace_ui/workspace_registry.py`
- `erp_workspace_ui/public/js/runtime/console/workspace_registry.js`
- `erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js`
- `erp_workspace_ui/warehouse_console/service.py`

Current source-backed facts:

- Warehouse has one protected home route: `/desk/warehouse-console`.
- Warehouse has four protected worklist queues under `/desk/warehouse-console-worklist/<queue-key>`:
  - `inbound-receiving`
  - `outbound-picking`
  - `stock-exceptions`
  - `movement-visibility`
- Warehouse has five protected detail/review route families:
  - `/desk/warehouse-console-receiving/<purchase-order>`
  - `/desk/warehouse-console-picking/<sales-order>`
  - `/desk/warehouse-console-stock-exception/<encoded-context>`
  - `/desk/warehouse-console-stock-posture/<encoded-context>`
  - `/desk/warehouse-console-movement/<encoded-context>`
- Current sidebar labels are flat: Overview, Inbound Receiving, Outbound Picking, Stock Exceptions, Movement Visibility.
- Current Overview panels are additive and route-specific. They work, but the route count now justifies a clearer cockpit model before adding transfer visibility.
- Warehouse Quick Find/Search remains intentionally absent.

### 2.2 Official / Vendor Sources Reviewed

Official/vendor sources used for IA direction:

- ERPNext Stock Entry documentation: https://docs.frappe.io/erpnext/user/manual/en/stock-entry
- ERPNext Stock Ledger documentation: https://docs.frappe.io/erpnext/v14/user/manual/en/stock/stock-ledger
- ERPNext Stock Transactions documentation: https://docs.frappe.io/erpnext/user/manual/en/stock-transactions
- Microsoft Dynamics 365 Warehouse Management workspace concepts: https://learn.microsoft.com/en-us/dynamics365/supply-chain/warehousing/warehouse-management-overview
- Microsoft Dynamics 365 warehouse-specific inventory transactions: https://learn.microsoft.com/en-us/dynamics365/supply-chain/warehousing/warehouse-transactions
- Oracle Fusion Inventory Management work area: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/26b/famml/inventory-management-work-area.html
- SAP Extended Warehouse Management monitor concept: https://help.sap.com/docs/SAP_EXTENDED_WAREHOUSE_MANAGEMENT

Design inferences:

- ERPNext stock documents are operational transaction documents, so the Warehouse Console should continue to expose only custom review routes unless a future owner-approved execution phase exists.
- Microsoft and Oracle inventory work areas separate task starts, exception management, and visibility/review activities. Warehouse W9 should adopt that separation.
- SAP EWM monitor-style UX supports a cockpit model that aggregates operations and exceptions without making every tile a transaction launcher.
- W9 should not copy native ERPNext modules; it should use the protected Workspace Console language and give Warehouse users a guided operational cockpit.

## 3. W9 Problem Statement

The Warehouse Console now has enough protected pages that the Overview risks becoming a stack of route-specific panels:

- Inbound Work.
- Outbound Work.
- Stock Exceptions.
- Movement Visibility.
- Detail/review pages behind each of those routes.

This is acceptable for incremental buildout, but it is not yet a serious premium operational cockpit. A warehouse user should not have to infer which page to use from implementation-phase terminology. The Overview should answer three questions quickly:

- What needs action or review now?
- What risks could block fulfillment or receiving?
- What changed in stock posture and where can I inspect it safely?

The IA should also make clear that the console is read-only: it is for visibility, review, and coordination, not posting stock.

## 4. Proposed W9A Scope

W9A should implement cockpit and navigation polish only.

Recommended included changes:

- Rework the Warehouse Overview into a cockpit layout with three pillar sections: Work To Do, Risks To Resolve, Movement To Understand.
- Replace route-by-route panel stacking with a concise operations command area.
- Keep current route labels, but group them visually and in sidebar metadata where safe.
- Add concise owner-facing copy that explains what each route is for.
- Add a top-priority strip that identifies the next best read-only review path from existing payloads.
- Add a "Warehouse pulse" summary using current overview payload data only.
- Add consistent object-card language across current queues and review pages.
- Preserve direct buttons to existing protected routes:
  - Open inbound receiving.
  - Open outbound picking.
  - Open stock exceptions.
  - Open movement visibility.
- Improve empty states so they explain what is healthy and what to inspect next.
- Preserve the existing read-only route model and detail routes.

Recommended excluded changes:

- No new backend domain method unless required to reshape the existing overview payload.
- No new queue route.
- No transfer visibility route.
- No Warehouse Search / Quick Find.
- No native ERPNext route targets.
- No Stock Entry, Purchase Receipt, Delivery Note, Pick List, Stock Reconciliation, reservation, or transfer execution actions.
- No valuation, accounting, GL, commercial, rate, amount, margin, cost, tax, billing, or payment fields.

## 5. Proposed Cockpit IA

### 5.1 Overview Structure

Recommended W9A Overview order:

1. **Command Header**
   - Title: `Warehouse Console`
   - Subtitle: short operational purpose, for example: `Review inbound, outbound, exceptions, and movements without leaving the protected Warehouse workspace.`
   - Status chips:
     - `Read-only`
     - `Warehouse workspace`
     - freshness timestamp

2. **Warehouse Pulse**
   - Four to six compact metrics derived from existing overview data.
   - Suggested metrics:
     - Receiving attention.
     - Picking attention.
     - Stock exceptions.
     - Movement records.
     - Active warehouse posture.
     - Freshness.
   - Avoid rates, amounts, costs, valuation, or stock value.

3. **Start Here**
   - A prioritized operational lane.
   - Shows 2 to 4 recommended read-only starts.
   - Examples:
     - `Review inbound due soon`
     - `Review outbound picking risk`
     - `Check stock exceptions`
     - `Inspect recent movement`
   - These are links to existing custom routes only.

4. **Work To Do**
   - Inbound Receiving and Outbound Picking as paired cards.
   - Copy should distinguish supplier-side receiving review from customer-side picking review.

5. **Risks To Resolve**
   - Stock Exceptions and Stock Posture language.
   - Stock Posture should be explained as detail context reached from exceptions, picking, receiving, and movement; not necessarily a standalone generic search.

6. **Movement To Understand**
   - Movement Visibility and Movement Review language.
   - The panel should explain movements as posted stock movement visibility, not a Stock Entry form.

7. **Workspace Guardrail Footer**
   - Short owner-facing line: `Warehouse Console is read-only in this phase. Posting and valuation stay in controlled ERP operations.`
   - This must not use developer phrases like `framework`, `backend`, `governed`, or `smoke`.

### 5.2 Sidebar Structure

Current sidebar is flat:

- Overview
- Inbound Receiving
- Outbound Picking
- Stock Exceptions
- Movement Visibility

Recommended W9A sidebar grouping:

- **Overview**
  - Overview
- **Operations**
  - Inbound Receiving
  - Outbound Picking
- **Risk**
  - Stock Exceptions
- **Visibility**
  - Movement Visibility

Do not add Stock Posture or Movement Review as primary sidebar items yet. They are context detail pages, not top-level start points.

### 5.3 Route Family Naming

Keep current protected route names. Do not rename accepted route keys.

Recommended user-facing labels:

| Current route | Current label | W9A display label | Notes |
| --- | --- | --- | --- |
| `/desk/warehouse-console` | Overview | Overview | Keep. |
| `/desk/warehouse-console-worklist/inbound-receiving` | Inbound Receiving | Inbound Receiving | Keep. |
| `/desk/warehouse-console-worklist/outbound-picking` | Outbound Picking | Outbound Picking | Keep. |
| `/desk/warehouse-console-worklist/stock-exceptions` | Stock Exceptions | Stock Exceptions | Keep. |
| `/desk/warehouse-console-worklist/movement-visibility` | Movement Visibility | Movement Visibility | Keep. |
| `/desk/warehouse-console-receiving/<purchase-order>` | Receiving Review | Receiving Review | Context detail only. |
| `/desk/warehouse-console-picking/<sales-order>` | Picking Review | Picking Review | Context detail only. |
| `/desk/warehouse-console-stock-exception/<encoded-context>` | Stock Exception Review | Stock Exception Review | Context detail only. |
| `/desk/warehouse-console-stock-posture/<encoded-context>` | Stock Posture Review | Stock Posture Review | Context detail only. |
| `/desk/warehouse-console-movement/<encoded-context>` | Movement Review | Movement Review | Context detail only. |

## 6. Premium UX Standard For W9A

W9A should feel like an intentionally designed operations cockpit, not a CRUD dashboard.

Visual direction:

- Use a warm warehouse operations palette already compatible with current Warehouse UI: off-white, slate, green/teal accents, amber risk accents.
- Keep strong hierarchy: command header, pulse metrics, start cards, grouped route cards.
- Avoid generic card grids with equal emphasis everywhere.
- Use compact but readable density; warehouse users need scan speed.
- Use consistent card affordances for route starts: title, operational description, state/metric, and one clear action.
- Avoid purple default SaaS styling and avoid overly dark control-room visuals unless separately owner-approved.
- Preserve responsive behavior: cockpit must work on desktop and mobile without horizontal overflow.

Interaction direction:

- Button text must be action-specific but read-only:
  - `Open inbound receiving`
  - `Open outbound picking`
  - `Open stock exceptions`
  - `Open movement visibility`
- Avoid execution verbs:
  - `Receive`
  - `Ship`
  - `Post`
  - `Submit`
  - `Transfer`
  - `Reconcile`
  - `Create`
  - `Save`
- No disabled fake execution buttons.

Copy direction:

- Use owner-facing operational language.
- Avoid developer-facing words:
  - `backend`
  - `frontend`
  - `framework`
  - `Frappe`
  - `smoke`
  - `test`
  - `governed`
  - `native ERP`
  - `route only`
  - `mutation`
- Never imply Warehouse Console can post or mutate stock.

## 7. Data Contract Guidance

W9A should reuse existing data where possible:

- Existing overview payload.
- Existing inbound summary.
- Existing outbound summary.
- Existing stock exception summary.
- Existing movement summary.
- Existing sidebar context.

If a small overview shape change is needed, it must remain bounded and read-only.

Allowed W9A data concepts:

- Counts.
- State labels.
- Due/aging labels.
- Warehouse names.
- Operational posture.
- Freshness timestamp.
- Custom route targets to current protected Warehouse routes.

Forbidden W9A data concepts:

- Stock value.
- Valuation rate.
- Incoming rate.
- Outgoing rate.
- Basic rate.
- Amount.
- Base amount.
- Transfer price.
- Stock queue.
- GL, accounting, cost, profit, margin, taxes, billing, payment, Item Price, or commercial pricing.
- Native route targets.
- Raw framework or exception text.

## 8. Smoke And Protection Expectations

W9A implementation must add or update focused smoke coverage for:

- Warehouse Manager Overview cockpit render.
- Warehouse User Overview cockpit render.
- Top-level route actions to inbound, outbound, stock exceptions, and movement visibility.
- Sidebar grouping, if the sidebar renderer exposes group semantics.
- Browser reload on `/desk/warehouse-console`.
- Repeated `/desk/warehouse-console` navigation idempotency.
- No duplicate Warehouse shells.
- No horizontal overflow at desktop and a mobile-width viewport.
- No Warehouse Quick Find/Search.
- No native ERP route href/action.
- No forbidden action labels.
- No valuation/accounting/commercial copy.

Required gates before commit/live:

- `python3 -m compileall erp_workspace_ui`
- `PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'`
- `node --check` for touched Warehouse runtime and smoke files.
- `python3 -m json.tool ui_smoke/package.json`
- `bash -n ui_smoke/run_playwright_docker.sh`
- `git diff --check HEAD`
- focused W9A Warehouse smoke with Warehouse Manager and Warehouse User.
- Sales freeze protection.
- full protected workspace source gate.
- runtime-only live alignment.
- focused W9A live smoke.
- full protected workspace live gate.

## 9. Main Control / Warehouse Agent Split

Main control agent owns:

- This W9 docs-only plan.
- Acceptance criteria.
- Credentialed focused smokes.
- Sales freeze and full protected gates.
- Commit/push.
- Runtime-only live alignment.
- Final protected live gate.
- Baseline documentation after acceptance.

Warehouse implementation agent owns only after this plan is accepted:

- Source-only W9A implementation.
- Source-only tests and focused smoke.
- Non-credentialed validation.
- Source handoff with changed-file list and exact credentialed smoke command.

Warehouse implementation agent must not:

- Commit.
- Push.
- Live-align.
- Run live sync.
- Modify Sales runtime.
- Modify Procurement runtime.
- Add stock execution, valuation, native escape, or Quick Find/Search.

## 10. Recommended W9A Agent Prompt

Use this only after owner approval:

```text
Implement Warehouse Console Phase W9A source-only: premium Warehouse Cockpit information-architecture polish.

Baseline:
- Branch: feature/erpnext-ui-design
- Protected W8B runtime: fb337a26d75af22d130fcb0bf43b779794bde055
- Smoke hardening: 20f6fbf3dc0c333f0e2381750f51ace8e0be8ecc
- W8B baseline docs: 5d225062b6c06d00fc64013e82eb35c18fc41576

Scope:
- Rework /desk/warehouse-console Overview into a premium cockpit with:
  - Command Header
  - Warehouse Pulse
  - Start Here
  - Work To Do
  - Risks To Resolve
  - Movement To Understand
  - read-only guardrail footer
- Group existing navigation mentally/visually:
  - Operations: Inbound Receiving, Outbound Picking
  - Risk: Stock Exceptions
  - Visibility: Movement Visibility
- Preserve existing route names and route ownership.
- Keep Stock Posture Review and Movement Review as contextual detail pages, not top-level sidebar starts.
- Reuse existing overview/sidebar data where possible. Only add bounded read-only overview fields if necessary.
- Add/update focused W9A smoke for Warehouse Manager and Warehouse User.

Strict exclusions:
- No new Warehouse route.
- No transfer visibility route.
- No Warehouse Quick Find/Search.
- No native ERPNext form/list/report/workspace escape.
- No Stock Entry, Purchase Receipt, Delivery Note, Pick List, Stock Reconciliation, reservation, reconciliation, serial/batch, or transfer execution action.
- No disabled fake execution buttons.
- No valuation/accounting/commercial fields or copy.
- No Sales runtime changes.
- No Procurement runtime changes.
- No commit, push, or live alignment.

Validation before handoff:
- python3 -m compileall erp_workspace_ui
- PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'
- node --check for touched Warehouse runtime and smoke JS
- python3 -m json.tool ui_smoke/package.json
- bash -n ui_smoke/run_playwright_docker.sh
- git diff --check HEAD
- static scans for native route escape, lifecycle/action labels, server write calls, valuation/accounting/commercial exposure, Quick Find/Search, and Sales/Procurement dirty boundary

If credentialed smoke is needed, stop and hand off this exact command:
cd /home/deploy/erp-projects/erpai_project1_erpnext_ui_design/impl_factory/05_custom_logic/custom_app/erp_workspace_ui
export ERPW_BASE_URL="https://meet.erpbosai.com"
export ERPW_WAREHOUSE_MANAGER_USERNAME="warehouse.manager@meet.com"
export ERPW_WAREHOUSE_MANAGER_PASSWORD="<owner-provided-password>"
export ERPW_WAREHOUSE_USER_USERNAME="warehouse.ygn.01@meet.com"
export ERPW_WAREHOUSE_USER_PASSWORD="<owner-provided-password>"
export ERPW_WAREHOUSE_W9A_ASSET_ROOT="$PWD"
export ERPW_PLAYWRIGHT_ARTIFACT_ROOT="/tmp/warehouse-phase-w9a-source-$(date -u +%Y%m%dT%H%M%SZ)"
npm --prefix ui_smoke run test:warehouse-w9a-cockpit:docker
```

## 11. Decision

Recommended decision: approve W9A before W8C.

Reason:

- Warehouse already has enough protected surfaces to justify a premium cockpit pass.
- Cockpit IA polish reduces owner/user confusion before adding transfer visibility.
- W9A can improve perceived quality without introducing new stock execution risk.
- W8C can follow with clearer placement in the `Movement To Understand` or future `Transfers` lane.

This W9 plan is documentation only.
