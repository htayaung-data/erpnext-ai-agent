# Finance & Accounting Cycle 2 GL / Trial Balance Scope and Implementation Plan

**Main Control authority:** Main Control v2

**Parent roadmap:** [Finance & Accounting Capability Map and Integration Plan](finance-accounting-capability-map-integration-plan-2026-07-17.md)

**Planning baseline:** `feature/erpnext-ui-design` at `cfdfe80a367a143b31a516f6076fc093c7355a07`

**Owner direction:** GL / Trial Balance source proof selected as the next Finance outcome

**Planning decision:** `planning_baseline_documented`

**Next explicit Owner gate:** `finance_cycle2_gl_tb_source_proof_authorized`

**State:** canonical source-only planning candidate; Finance Cycle 2 implementation is not started

**Date:** 2026-07-17

## 1. Purpose and authority

This document is the canonical scope and implementation plan for the Owner-selected Finance Cycle 2 direction: a trustworthy, permission-controlled, read-only General Ledger / Trial Balance source proof and bounded Finance posture.

The Owner has selected the direction and approved the five-phase documentation structure. Acceptance of this completed document remains the scope gate before any Cycle 2 source-proof task is declared active. This document does not itself authorize installed-source inspection outside an approved read-only task, runtime implementation, staging, commit, push, live alignment, metadata, permission changes, protected gates, or accounting execution.

The authoritative planning chain is:

1. accepted Main Control v2 transition handoff;
2. accepted Codex Delivery Operating Model V1 pilot;
3. accepted and pushed Finance Capability Map and Integration Plan;
4. this Cycle 2 scope and implementation plan;
5. later mini-phase evidence and closure artifacts, created only when their mini-phase is actually authorized and performed.

Later accepted artifacts supersede stale historical phase labels. Current committed source remains decisive if it contradicts documentation. The source repository remains authoritative; the live deployment tree is outside this planning task.

The current documentation candidate is exactly this plan plus the documentation README. The four accepted unrelated exclusions remain outside every candidate allowlist:

1. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py`
2. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/browser_supplier_payables_fixture_diagnostic.py`
3. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/ui_smoke/sales_final_acceptance_audit.js`
4. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/a.out`

## 2. Business outcome

Cycle 2 is intended to establish a bounded financial-control posture that answers, for one authorized company and one exact financial context:

- what the opening debit and credit totals are at the reporting start;
- what debit and credit movement occurred during the reporting period;
- what the closing debit and credit totals are at the reporting end;
- whether the authoritative Trial Balance result is mathematically balanced;
- whether the bounded Trial Balance result reconciles to the approved GL source and declared report semantics;
- which context, source version, Finance Book, currency, period, and dimensions governed the result;
- whether the result is ready, restricted, unsupported, unavailable, or an integrity exception without leaking detailed ledger identities.

The outcome is a control and foundation result. It is not a General Ledger browser, native Trial Balance replacement, financial statement, close process, cash dashboard, consolidation engine, or accounting action surface.

## 3. Explicit non-goals and deferred scope

The following remain deferred unless the Owner later approves a distinct scope contract:

- GL Entry, voucher, party, journal, employee, bank, tax, customer, supplier, or transaction rows;
- account drilldowns, native report/list/form routes, account-tree navigation, or report passthrough;
- export, download, print, email, notification, attachment, sharing, or portal exposure;
- Balance Sheet, Profit and Loss, Cash Flow, ratios, management reports, certification, or publication;
- Period Closing Voucher creation, fiscal restriction, close, reopen, adjustment, journal, reposting, correction, or write-off;
- cash/bank amounts, reconciliation, payment preparation, payment release, or bank actions;
- multi-company, intercompany, consolidation, elimination, presentation currency, or exchange-rate revaluation;
- budgeting, forecasting, tax filing, inventory/COGS, fixed assets, payroll, financing, or other downstream accounting domains;
- new roles, role assignments, User Permissions, Page/Report permissions, metadata, or master-data changes;
- Finance-to-AI access, AI summaries, report tools, accounting recommendations, or any AI authority;
- changes to Sales, Procurement, Warehouse, Shared UI, routing, registries, or governance unless separately justified and approved;
- any accounting execution or operational-data action.

No deferred capability becomes implicitly approved because its source fields or report filters are encountered during source proof.

## 4. Fixed design principles

### 4.1 Accounting truth

- Financial semantics will be proven from the installed ERPNext/Frappe version and authoritative product source, not inferred from labels or field names.
- Voucher truth, report truth, account-hierarchy truth, opening-balance truth, Period Closing Voucher truth, and presentation truth are distinct until reconciled.
- Native report output may be an internal proof input; it will never be passed through directly to the browser.
- An aggregate is not authoritative until source lifecycle, date, period, currency, book, dimension, permission, consistency, and reconciliation rules are exact.
- Unsupported semantics fail closed without partial totals.

### 4.2 Authority and privacy

- Browser company, default company, filters, route state, cached context, `System Manager`, Executive, Sales, Procurement, Warehouse, or AI roles never grant Finance authority.
- Role authority is necessary but insufficient; company, period, source DocType/report, field, account class, Finance Book, and dimension authority are also required.
- No new GL/TB data role is assumed. C2A must decide whether an existing Accounts Manager role, a future Controller/Auditor role, or another bounded purpose is appropriate.
- Accounts User retains the current shell/unavailable posture unless explicitly approved otherwise.
- Sensitive account classes and sparse dimensional slices require an explicit visibility or suppression policy before presentation.

### 4.3 Read-only and execution boundary

- Cycle 2 is read-only.
- Approval never implies posting; report availability never implies export; balance visibility never implies journal, close, or correction authority.
- Refresh may re-read the same authorized contract and has no accounting effect.
- Every future write or operational effect remains a separate Tier 3 outcome with action-time authorization, maker-checker, idempotency, immutable audit, recovery, and reconciliation.

### 4.4 Shared UI and workspace protection

- Finance owns accounting semantics, data contracts, roles, company context, copy, and page composition.
- Shared UI owns neutral lifecycle, shell, sidebar/header/filter grammar, request isolation, accessibility, responsiveness, focus, and teardown contracts.
- The default implementation changes no Shared UI file. A discovered shared gap becomes a separate impact decision, not an incidental Cycle 2 edit.
- Existing Sales, Procurement, Warehouse, and Finance behavior must not be broken, replaced, broadened, or cleaned up incidentally.
- Landing precedence remains `Sales > Procurement > Finance > Warehouse`.
- Existing Finance search remains disabled and existing Overview/Refresh governance remains unchanged unless a later exact scope explicitly requires otherwise.

### 4.5 Exact no-broadening checklist

- No new Finance route, sidebar item, search surface, report catalogue, registry target, landing change or native exception by default.
- No company selector or multi-company inference without a separate Owner-approved authority model.
- No GL Entry row, account identity/number, voucher, party, narration or drilldown.
- No native General Ledger or Trial Balance report route/passthrough.
- No list, form, export, download, print, email, notification or AI surface.
- No journal, repost, close, reopen, correction, reconciliation, payment or other execution.
- No statement, cash/liquidity, tax, consolidation, budget or management-reporting expansion.
- No Cycle 1 AR/AP semantic, role, payload or presentation rewrite.
- No copying or editing Sales, Procurement or Warehouse adapters for visual consistency.
- No opportunistic registry, governance, shared CSS, historical-label or runtime cleanup.

## 5. Authoritative references and source-proof candidates

Repository authority includes:

- `main-control-v2-transition-handoff-2026-07-16.md`
- `codex-delivery-operating-model-v1-pilot-2026-07-16.md`
- `finance-accounting-capability-map-integration-plan-2026-07-17.md`
- `finance-accounting-phase-f6f-cycle1-final-validation-closure-readiness-2026-07-16.md`
- `shared-core-workspace-adapter-contract-v2.md`
- `shared-component-and-implementation-golden-rule-standard-v1.md`
- `enterprise-shared-ui-component-standard-v1.md`
- `enterprise-shared-ui-component-implementation-contract-v1.md`
- `frozen-workspace-protection-package-standard-v1.md`
- `warehouse-console-phase-w13a-premium-ui-visual-standard-2026-06-10.md`
- formal Sales and Procurement protection artifacts and accepted Warehouse closure artifacts.

Primary official product references include:

- [ERPNext Accounting Reports](https://docs.frappe.io/erpnext/accounting-reports)
- [ERPNext General Ledger](https://docs.frappe.io/erpnext/general-ledger)
- [Opening Balance in Accounts](https://docs.frappe.io/erpnext/opening-balance)
- [Period Closing Voucher](https://docs.frappe.io/erpnext/period-closing-voucher)
- [Accounting Period](https://docs.frappe.io/erpnext/accounting-period)
- [Journal Entry and immutable-ledger note](https://docs.frappe.io/erpnext/journal-entry)
- [Frappe Users and Permissions](https://docs.frappe.io/framework/user/en/basics/users-and-permissions)
- [Frappe Database API permission distinction](https://docs.frappe.io/framework/user/en/api/database)

Official documentation establishes useful boundaries: ERPNext Trial Balance presents opening debit/credit, period debit/credit, and closing debit/credit in company base currency; debit and credit totals should match; report options may affect Period Closing Entries, zero-balance accounts, unclosed prior-year P&L, Finance Book, Cost Center, and other context. Installed-version behavior still must be proven before use.

Candidate installed sources to fingerprint and inspect in C2B include:

- Trial Balance and General Ledger `.py`, `.js`, and `.json` report implementations and metadata;
- `financial_statements.py`, `accounts/utils.py`, and `accounts/general_ledger.py` behavior used by those reports or postings;
- `GL Entry` and `Account` metadata/controllers, lifecycle, fields, indexes, hierarchy, cancellation/immutable-ledger behavior, and permission paths;
- `Account Closing Balance` and `Period Closing Voucher` metadata/controllers, asynchronous processing status, cache creation and reconciliation;
- `Company`, `Fiscal Year`, `Accounting Period`, `Accounts Settings`, `Finance Book`, Currency and precision settings;
- Cost Center, Project, Accounting Dimension and active installed dimension metadata/controllers;
- Frappe report execution, reportview/match-condition, Page/Report, DocType/field/User Permission and database-query paths;
- exact installed app Git revisions, dirty state and SHA-256 for every selected source file.

### 5.1 Accepted source-safety gates

The bounded accounting review found evidence-backed risks in upstream ERPNext v16.4.1 that C2B must recheck against the exact installed fingerprints:

- The native General Ledger report loads Customer, Supplier and Employee party-name maps using `frappe.get_all`. Frappe documents that `get_all` does not apply user permissions. The native GL report is therefore an internal privileged reconciliation oracle only and is excluded from the runtime aggregate path.
- Native Trial Balance movement logic applies match conditions in one path, while account-tree, opening-balance, closing-cache and dimension-expansion paths use different direct SQL/Query Builder/`get_all` behavior. Desk report metadata does not automatically secure a custom service import. Opening, movement, account, company and dimension authorization must be proven independently; any mismatch rejects direct report reuse.
- A submitted Period Closing Voucher is insufficient. If its processing status is not `Completed`, its Account Closing Balance set is absent/incomplete/duplicate, or cache-to-GL reconciliation fails, the result is unavailable. There is no silent partial-opening fallback.
- Debit-equals-credit is a full-context assertion, not a universal statement for account-, party-, Cost Center-, Project-, custom-dimension-, sensitive-account- or permission-filtered slices. The initial runtime candidate is therefore one authorized company, complete authorized chart, company base currency, one explicit Finance Book mode, and no account/party/dimension slice.
- A `balanced` claim requires complete-chart authority. If account permissions or sensitive-account suppression remove any ledger account, the service does not calculate a visible-subset Trial Balance and call it balanced; the integrity posture is unavailable.
- Requested dates outside the accepted fiscal context are rejected. Native report date clamping or message-based rewriting is not inherited.
- Native `flt` arithmetic is not the public precision contract. The existing Finance Decimal-string, installed currency-precision and System Settings rounding discipline applies before any difference is evaluated.
- Finance Book mode is explicit. Blank/NULL entries, company default book and a selected non-default book require proven inclusion rules; `all books` is never an implicit union.
- `ignore_is_opening_check_for_reporting`, `ignore_account_closing_balance`, PCV mode, company default Finance Book, active Accounting Dimensions and every source hash are semantic fingerprint inputs.

### 5.2 Adapter decision

C2B7 must choose one path or stop:

1. **Controlled reconstruction adapter:** preferred candidate; reconstruct the bounded full-company/full-chart aggregates from permission-preserving authoritative sources with exact hierarchy, opening/PCV/cache, consistency, cap and parity proof.
2. **Separately proven Trial Balance adapter:** possible only if the exact installed version proves equivalent authorization for opening, movement, account, company, book and every enabled dimension, validates all internal output, and introduces no identity-bearing query. Upstream report metadata alone is insufficient.
3. **Stop:** if neither approach preserves accounting semantics, complete-chart authority, consistency, performance and a safe public contract.

The native GL report remains an oracle only. Native report passthrough, unrestricted raw SQL/`frappe.get_all`, browser-side aggregation and visible-subset balance claims are rejected design shortcuts.

## 6. Target posture hypothesis

The following is a hypothesis to prove, not an approved runtime schema.

### 6.1 Candidate context

- authorized company ID and display label;
- company/base currency;
- exact `from_date`, `to_date`, and as-of meaning;
- fiscal year and accounting-period status;
- explicit Finance Book mode and inclusion/exclusion rule, never an implicit all-books union;
- initial `dimension_mode: none`; Cost Center, Project and custom-dimension semantics are source-proven but runtime-filtered slices remain deferred;
- explicit PCV/opening policy and Account Closing Balance cache posture;
- installed source/report version and consistency/reconstruction identifier;
- generated-at time under the declared consistency mode;
- role/purpose classification without exposing the user or raw role list.

### 6.2 Candidate integrity controls

- opening debit and opening credit totals;
- period debit and period credit totals;
- closing debit and closing credit totals;
- opening, movement, and closing balance indicators under approved precision;
- precision-normalized opening, movement and closing debit/credit differences;
- Trial Balance-to-GL reconciliation status;
- source freshness and declared consistency mode;
- controlled reason code for unsupported, restricted, unavailable, or integrity-exception states.

### 6.3 Optional category summaries

Assets, Liabilities, Equity, Income, and Expense summaries may be considered only after C2B proves installed hierarchy mapping and C2C approves sensitive-account and sparse-slice policy. Account names, account numbers, balances by leaf account, party data, vouchers, and drilldowns remain deferred.

### 6.4 Serialization

- Financial amounts use fixed decimal strings, never binary floats.
- Currency precision and rounding come from the installed authoritative contract.
- Dates use exact ISO date-only strings unless installed behavior proves a required timestamp boundary.
- Booleans, enumerations, arrays, and objects use exact allowlists; unknown keys fail closed.
- No source identity needed only for internal reconciliation is returned publicly.

The canonical signed invariant is:

```text
(opening_debit - opening_credit)
+ (period_debit - period_credit)
= (closing_debit - closing_credit)
```

For the approved full-company, complete-chart, base-currency and explicit-book context, the precision-normalized opening, movement and closing debit/credit differences must also be zero. These assertions are not reinterpreted for future filtered slices; filtered-slice balance claims require a new contract. Public copy must state that the result is neither closed, audited, certified nor a financial statement.

## 7. Five-phase implementation plan

### Pre-cycle Gate C2P — Plan acceptance

This document and its README entry are the only C2P candidate. Owner acceptance of the exact plan closes the pre-cycle planning gate and authorizes Main Control to propose the first bounded C2A/C2B task. It does not activate C2A, start Finance Cycle 2, or authorize source proof. Only a later explicit `finance_cycle2_gl_tb_source_proof_authorized` decision may start the cycle. It does not automatically authorize runtime work, staging, commit, push, live access, or any later mini-phase.

### Phase C2A — Scope and governance

| Mini-phase | Objective and bounded work | Required evidence/output | Exit gate |
| --- | --- | --- | --- |
| C2A1 Baseline and authority | Reverify source path, branch, HEAD/upstream, index, exclusions, parent documents, installed-version receipts, Cycle 1 closure, and protection status. Record which mutable facts require fresh proof. | Point-in-time source receipt; exact exclusions; authority chain; no live claim. | No baseline or authority contradiction. |
| C2A2 Business outcome and materiality | Confirm intended users, decisions supported, reporting frequency, acceptable freshness, materiality/tolerance language, and whether integrity exception visibility is useful without detail. Freeze non-goals. | Owner fact sheet; business outcome; explicit unavailable/exception expectations. | Owner confirms business purpose without adding statements, close, execution, or rows. |
| C2A3 Financial context | Define authorized company, base currency, dates, fiscal year, period status, Finance Book, Cost Center, Project, installed dimensions, source version, and consistency token. Identify unsupported context. | Canonical `financial_context` schema and validation table. | Every context value has source, authority, serialization, and fail-closed rule. |
| C2A4 Role, SoD, and data classification | Decide viewer purpose, candidate roles, company/account/dimension authority, sensitive account classes, sparse-slice policy, Auditor posture, prohibited combinations, and whether Accounts Manager is sufficient. | Role-purpose matrix; data classification; denial rules; no permission change. | Owner accepts role design or scope stops before data exposure. |
| C2A5 Ownership, files, gates, and scope closure | Freeze source-proof allowlist, likely runtime ownership locks, specialist tasks, test categories, protection triggers, and sequential approval gates. | Accepted scope contract; exact next-task allowlist; C2A closure receipt. | Explicit Owner authorization for C2B source proof. |

Phase C2A changes documentation only. It does not inspect operational data, change roles, or create a runtime endpoint.

### Phase C2B — Installed ERPNext source proof

| Mini-phase | Objective and bounded work | Required evidence/output | Exit gate |
| --- | --- | --- | --- |
| C2B1 Installed source inventory | Pin exact ERPNext/Frappe Git revisions and dirty state; hash Trial Balance/GL report files, financial statements/accounting utilities, GL Entry/Account, Account Closing Balance/PCV, fiscal/settings, book/dimension and Frappe report/permission/query paths. | Reproducible installed-source manifest with exact paths/functions/hashes and official reference crosswalk. | Installed code, not an upstream tag assumption, is authority; every source is located or declared absent. |
| C2B2 GL Entry lifecycle proof | Prove included/excluded GL Entry states, cancellation/immutable-ledger behavior, posting date/time, fiscal context, opening markers, voucher lineage, company/account currency fields, Finance Book, dimensions, and malformed/duplicate behavior. | Field/lifecycle matrix; permission path; bounded fixtures; unsupported-state list. | Authoritative GL read contract is possible, or stop. |
| C2B3 Trial Balance algorithm proof | Trace opening, period movement, closing, account hierarchy, group/ledger rollup, zero-account filtering, debit/credit netting, root types, accumulated/unclosed P&L, and report totals. | Algorithm narrative; formula table; installed filters/defaults; expected columns/types. | Opening/movement/closing and total-equality semantics are exact. |
| C2B4 Fiscal and closing proof | Prove Fiscal Year boundaries, mid-year starts, opening entries, prior-year carry-forward, PCV inclusion/exclusion, multiple/cancelled/late/in-progress/failed PCVs, processing status, Account Closing Balance completeness/duplicates/cache-to-GL parity, Accounting Period/frozen status, and later postings. | Fiscal/PCV/cache scenario matrix and authoritative as-of policy. | No partial cache, unexplained prior-period or P&L carry-forward behavior. |
| C2B5 Currency, Finance Book, and dimensions | Prove company base-currency behavior, account/document currency effects, Decimal precision/rounding/near-zero rules, no/default/non-default/blank Finance Book behavior, and Cost Center/Project/custom-dimension intersection/tree/disabled/historical behavior. | `financial_context.v1`; explicit book and dimension modes; unsupported combinations. | Initial runtime remains base currency, explicit book and no dimension slice; unsupported context fails closed. |
| C2B6 Permission, consistency, and performance | Prove opening and movement resolve the identical authorized complete-chart scope; compare report/Page and DocType/row/field permission paths; reject bypasses; determine snapshot/reconstruction consistency; establish caps, query plan, timing budget, PCV concurrency and change detection. | Permission call graph; report-versus-reconstruction evidence; consistency decision; caps/performance/threat notes. | One safe complete-chart adapter approach survives, or stop. |
| C2B7 Source selection and proof closure | Compare controlled reconstruction against native Trial Balance and bounded GL/Account Closing Balance oracles; record parity, residual gaps, version coupling, reversibility, likely files and rejected native paths. | One source-proof matrix and synthesis; selected/rejected approach with C2C inputs. | Any unresolved evidence-backed High stops; otherwise `gl_tb_source_proof_ready_for_contract`. |

C2B is read-only source proof. It does not create or expose a Finance endpoint, UI, role, report, or live change.

### Phase C2C — Accounting, permission, and public-contract design

| Mini-phase | Objective and bounded work | Required evidence/output | Exit gate |
| --- | --- | --- | --- |
| C2C1 Canonical source adapter contract | Freeze selected sources, installed-version coupling, filters, lifecycle states, hierarchy rules, consistency mode, caps, and source error handling. | Versioned adapter contract and exact internal schema. | No unresolved source-semantic dependency. |
| C2C2 Accounting invariants | Define the signed opening-plus-movement-equals-closing equation, full-company/full-chart debit-credit equality, group/ledger rollups, GL-to-TB parity, PCV/cache treatment, precision normalization, zero behavior, and exception ownership. Disable rather than reinterpret full-TB assertions for any future filtered slice. | Invariant catalogue and fixture oracle; accountant sign-off. | Every public total has a reproducible context-bound invariant. |
| C2C3 Failure and reconciliation taxonomy | Separate unauthorized, restricted, unsupported, unavailable, source error, malformed source, inconsistent context, concurrent change, and accounting integrity exception. Decide which states may safely show context or totals. | Exact reason-code registry; no-partial-data table; reconciliation boundary. | Browser cannot mistake absence, failure, or exception for a valid zero/balance. |
| C2C4 Role/company/account/dimension authority | Freeze viewer roles, one-company resolution, complete-chart requirement, report/DocType/field gates, sensitive-account policy, explicit book mode, no-dimension initial mode, cache invalidation, and action prohibition. If an approved user cannot see the complete chart, return unavailable rather than a visible-subset balance. | Permission matrix, data classification, denial-first sequence, threat model. | Security review accepts the complete-context read boundary. |
| C2C5 Exact public response contract | Define exact context, integrity totals, optional category summaries, fixed decimal/date types, policy metadata, forbidden identity/action keys, and maximum payload. | Public JSON schema and browser validation contract. | Unknown keys/types and forbidden identities fail closed. |
| C2C6 UI and integration contract | Freeze information hierarchy, state copy, filters, refresh behavior, shared component use, route/registry/governance posture, accessibility, responsive requirements, and protection triggers. | Approved UI contract and wire-level state matrix; no runtime code. | Accounting truth and authority cannot be broadened by presentation. |
| C2C7 Independent design reviews and synthesis | Run bounded accounting, security/leakage, Shared UI/protected-workspace, architecture, and release reviews. Accept Blocker/High only with evidence and synthesize once. | Accepted/rejected/deferred finding register; implementation readiness decision. | Explicit Owner approval for exact C2D implementation scope. |

### Phase C2D — Bounded runtime and premium Finance UI

| Mini-phase | Objective and bounded work | Required evidence/output | Exit gate |
| --- | --- | --- | --- |
| C2D1 Finance-owned adapter scaffold | Prefer a dedicated Finance-owned GL/TB adapter if repository structure and review permit; otherwise lock the existing Finance service to one writer. Add no public output yet. | Minimal module/service boundary; import and isolation tests. | No shared or protected-workspace edit; no source bypass. |
| C2D2 Accounting computation | Implement the selected source adapter, exact financial context, source validation, invariants, reconciliation, caps, fixed decimals, and fail-closed reasons. | Backend tests for every source fixture and invariant. | No partial or unreconciled ready result. |
| C2D3 Resolver and endpoint | Apply authentication, role-purpose, selected-company, report/DocType/field, period/book/dimension, source and response gates before reads. Expose one read-only endpoint. | Denial-first tests; exact endpoint schema; no guest or bypass path. | Wrong authority cannot trigger financial source reads. |
| C2D4 Browser contract and request isolation | Validate raw payload before normalization; reject unknown/forbidden keys and non-finite/malformed values; clear stale data on refresh, supersession, error, route departure, hide, logout/user switch, or authority change. | Browser schema tests and lifecycle smoke. | Stale or malformed financial data cannot remain visible. |
| C2D5 Premium Finance presentation | Compose the approved context band, integrity summary, opening/movement/closing cards, optional category summary, methodology/availability explanation, and Refresh/status behavior inside the existing Finance page. | Screenshot-independent DOM/state assertions and copy review. | No row, native route, export, action, or misleading certification language. |
| C2D6 Responsive and accessible behavior | Validate semantic headings, landmark/order, contrast, visible focus, keyboard navigation, polite persistent status, focus restoration, reduced motion, zoom, and 1440px/1366px, 1024px/860px, 390px and 320px behavior. | Renderer and accessibility evidence; no independent document horizontal scroll. | Accepted behavior at required viewport/state combinations. |
| C2D7 Registry, governance, and integration alignment | Change registry/governance only if the accepted contract requires exact new Finance section metadata; preserve route, landing precedence, search-disabled posture, Overview/Refresh-only action boundary, cache keys, and workspace isolation. | Parity tests and exact diff; protection-trigger decision. | No incidental shared/runtime or workspace broadening. |
| C2D8 Source acceptance | Run full scoped tests, static checks, lifecycle/responsive smokes, and bounded counterpart reviews; remediate evidence-backed findings once. | Source acceptance receipt and exact candidate allowlist. | Explicit Owner staging decision; no automatic external state. |

### Phase C2E — Validation, release, live acceptance, and closure

| Mini-phase | Objective and bounded work | Required evidence/output | Exit gate |
| --- | --- | --- | --- |
| C2E1 Accounting and source verification | Re-run invariant fixtures, adapter/report parity, fiscal/PCV, currency/book/dimension, malformed/concurrent, cap/performance and version checks at the accepted source revision. | Final accounting/source evidence bundle. | No unexplained discrepancy or unsupported ready state. |
| C2E2 Permission and leakage verification | Run guest/wrong-role/role-combination/company/report/DocType/field/account-class/dimension denials, exact-schema and recursive identity/action rejection, stale-authority and cache isolation tests. | Security evidence and no-authority receipt. | No open Blocker/High. |
| C2E3 Finance and protected regression | Run Finance tests and lifecycle smoke; if Shared UI/routing/registry/governance triggers exist, run formal Sales/Procurement and applicable Warehouse/Finance gates. | Trigger matrix and regression evidence. | Existing accepted workspace behavior remains intact. |
| C2E4 Premium UI renderer evidence | Exercise loading, ready, empty, restricted, unavailable, error, rejected-payload and refresh states at 1440px/1366px, 1024px/860px, 390px and 320px using production renderer contracts. | Screenshot-independent renderer and accessibility receipt. | UI is consistent, truthful, accessible and responsive. |
| C2E5 Final bounded review and synthesis | Accounting, security, Shared UI/integration and release reviewers inspect the exact final hashes once. | Final finding disposition and source-closure recommendation. | No open evidence-backed Blocker/High. |
| C2E6 Staging, commit, and push gates | Under separate approvals, stage exact files, verify cached manifest/diff/check, commit exact candidate, then separately push and verify upstream. | Separate staging, commit and push receipts. | Each gate explicitly approved and verified. |
| C2E7 Live alignment and authenticated acceptance | Under separate approval, compare source/live, align only exact files, perform only required operational actions, and gather authenticated allowed/denied role evidence. | Exact hashes, intentional drift record, browser evidence, rollback/recovery receipt. | Source tests/smoke are not substituted for live acceptance. |
| C2E8 Cycle 2 closure | Reconcile scope, source, commit/push, live, permissions, metadata, protected gates, remaining risks and deferrals. Record next-cycle decision separately. | Cycle 2 closure document and canonical roadmap update. | Owner accepts closure; no next cycle starts automatically. |

## 8. Source-semantic proof register

C2B must answer every question below with installed-source evidence or mark the affected capability unsupported.

| Topic | Questions that must be resolved |
| --- | --- |
| Reporting dates | Is opening evaluated before `from_date` or as of its start? Are posting time and future-dated rows relevant? How are inclusive boundaries and timezone handled? Invalid/out-of-year requests are rejected, never silently clamped. |
| Opening entries | How are `is_opening` entries, migration/opening invoices, Temporary Opening, and fiscal-year-agnostic opening behavior represented? |
| Period closing | How are PCV rows included/excluded? What happens with multiple/cancelled/late/in-progress/failed PCVs and post-PCV entries? Is the selected PCV `Completed`, is its Account Closing Balance set complete and unique, and does cache reconcile to GL? How is unclosed prior-year P&L presented? |
| Cancellation/amendment | Which immutable-ledger cancellation/reversal rows remain, how are they paired, and which report filters exclude/include them? |
| Debit/credit netting | Are account values independently shown as debit/credit or netted? How are negative, zero, and malformed values treated? |
| Hierarchy | How are Group versus Ledger accounts rolled up? Which root types map to categories? How are disabled, renamed, merged, malformed, or cross-company accounts handled? |
| Finance Book | What is the explicit mode, how are blank/NULL/default/non-default books treated, and does inclusion/exclusion preserve exact totals? `All books` is never implicit. |
| Dimensions | How do Cost Center, Project, and custom Accounting Dimensions filter or roll up? Are tree descendants included? What permission intersection applies? |
| Currency | Are Trial Balance figures strictly company base currency? Which precision and rounding settings apply? Can account/document currencies affect parity or only source validation? |
| Consistency | Can report and supporting reads share one snapshot? If not, what reconstruction token or concurrency detection prevents mixed-time results? |
| Permissions | Which Page/Report, DocType, field, row/User Permission and account/dimension gates apply to report execution and underlying reads? Do opening and movement resolve the identical complete authorized chart? |
| Semantic settings | What values apply for `ignore_is_opening_check_for_reporting`, `ignore_account_closing_balance`, PCV mode, company default Finance Book, active dimensions, precision and rounding? Are all recorded with source hashes? |
| Volume/performance | What row/account caps, query counts, memory/latency budgets, timeouts and oversized-result behavior are safe? |
| Integrity exception | Does an unbalanced or unreconciled result safely expose aggregate context/totals, or must all totals be suppressed? C2C must decide using accounting and privacy evidence. |

## 9. Premium UI and shared-contract design

Premium means calm information hierarchy, precise financial context, truthful state communication, accessible interaction, responsive composition, and visual consistency with the accepted enterprise workspaces. It does not mean ornamental charts, dense tables, native-report imitation, or additional actions.

The default archetype is the existing Finance Control Desk **workspace home**, not a new report route or shared report shell. The accepted route `/desk/finance-control-desk`, Overview active state, Finance landing behavior and Finance-owned presentation/lifecycle shell remain in place. A new route would unnecessarily trigger routing, registry, governance, sidebar and shared report-shell risk before a genuine shared need is proven.

C2C6 must select one context interaction mode:

- **`backend_fixed`:** authorized company, period, Finance Book and dimensions are quiet non-interactive context facts; Refresh is the only command.
- **`bounded_selectable`:** company remains locked; only approved Date From/Date To, Finance Book and dimension controls are shown, in the order Apply, Reset, Refresh. Browser values remain requests, never authority.

No account, voucher or party lookup and no generic Finance search is permitted in either mode.

### 9.1 Proposed page composition

1. **Existing managed workspace shell:** unchanged shared sidebar, header, lifecycle, route and landing behavior.
2. **Financial context band:** authorized company, base currency, exact period/as-of, Finance Book and dimension posture. Context is display-only unless a separately approved bounded filter is provided; the server remains authoritative.
3. **Integrity hero:** balanced, integrity exception, restricted, unsupported or unavailable state with business-facing explanation. Never say audited, certified, final, closed, or reconciled unless the exact underlying contract proves that word.
4. **Opening / movement / closing summary:** three calm cards, each showing Debit, Credit and Difference using right-aligned tabular numerals, fixed decimal presentation and consistent card grammar.
5. **Accounting control checks:** business-facing text results for opening plus movement equals closing, debit equals credit, bounded GL/TB agreement, complete hierarchy rollup and consistent period/book/dimension application.
6. **Optional category summary:** only approved root-category aggregates, with sparse/sensitive handling and no account navigation.
7. **Existing Cycle 1 working-capital posture:** preserve accepted AR/AP cards, semantics, role behavior and order without opportunistic rewriting or cleanup.
8. **Method and availability panel:** source, period, book/dimension coverage, excluded semantics and freshness without exposing technical internals or identities.
9. **Read-only boundary:** state that the page provides posture only and does not post, close, export, reconcile or open transaction detail.
10. **Existing Refresh and persistent status behavior:** read-only refresh, one authoritative status region, bounded focus restoration and stale-result clearing.

No chart is planned for this source-proof cycle. A chart adds visual weight without improving the primary integrity and reconciliation decision.

### 9.2 Required states

- transient loading within the authoritative render host;
- `ready` only when authority, context, precision and reconciliation checks pass;
- `empty` only for a valid proven zero-activity period, never as a missing-value substitute;
- `restricted` for role, company, book, dimension or direct-route denial without revealing hidden options;
- `unavailable` for unsupported semantics, incomplete hierarchy, inconsistent context, reconciliation failure or rejected payload;
- `error` for a short business-safe transport/runtime failure;
- superseded refresh and route-departure teardown, which never render stale data.

An accounting balance or reconciliation failure must never be styled as normal ready success. A GL/TB-specific unavailable state may coexist with still-valid Cycle 1 posture only when the common role/company context remains valid and the exact public schema explicitly supports independent section states.

Every state must define visible copy, DOM/schema, focus behavior, announcement behavior, retained/cleared values, and permitted actions. Unavailable and restricted are not displayed as zero.

### 9.3 Consistency and responsiveness

- Reuse shared spacing, typography, color tokens, cards, status treatments, filter grammar and responsive rules already accepted by other workspaces.
- Do not copy Sales/Procurement/Warehouse page-local business logic or create Finance-specific duplicates of shared primitives.
- Preserve semantic reading order as cards reflow at 1440px/1366px desktop, 1024px/860px transition, 390px mobile and 320px narrow mobile.
- No independent document horizontal scroll; any approved dense content must use a local, labeled, keyboard-accessible overflow region.
- No nested vertical scroll; `.main-section` remains the natural Desk scroll owner and the Finance live-status remains locally contained.
- Verify 200% zoom/reflow, text expansion, visible focus, contrast, reduced motion and persistent status behavior.
- Do not claim authenticated screen-reader or forced-colors acceptance unless those checks are actually performed; otherwise carry the deferral explicitly.
- Visual polish must not hide unavailable semantics, compress financial labels into ambiguity, or make category summaries appear actionable.

### 9.4 Shared UI trigger rule

If implementation cannot satisfy the approved design using current shared contracts, Main Control stops the Finance change and produces a separate Shared UI impact proposal. That proposal requires exact shared files, three-or-more-workspace impact analysis where relevant, formal Sales/Procurement and applicable Warehouse/Finance regression evidence, independent review, and separate live approval. It is not bundled into Cycle 2 by convenience.

## 10. Role, company, permission, and data-classification plan

No role or permission is approved by this document. C2A4 must resolve the following candidate posture before source data can be exposed.

| Authority subject | Planning posture |
| --- | --- |
| Guest | Always rejected before any context or source read. |
| Non-Finance role | Rejected; Sales, Procurement, Warehouse, Executive, System Manager, or AI authority is not inherited. |
| Accounts User | Retains current shell/unavailable posture unless the Owner explicitly approves a bounded GL/TB purpose. |
| Accounts Manager | Existing Cycle 1 aggregate role; may be evaluated but is not automatically authorized for GL/TB. |
| Controller candidate | Potential aggregate integrity and category-summary role; role existence, company scope, account classes, and SoD must be approved before implementation. |
| Auditor candidate | Potential read-only integrity role; audit purpose does not imply all companies, rows, sensitive accounts, reports, exports, or execution. |
| System Manager | Administration alone is not a Finance data bypass. |
| Break-glass | Not part of the read-only posture; future authority requires explicit emergency policy and immutable audit. |

Company authority remains server-resolved. The current one-company Cycle 1 contract is a safe limitation, not a multi-company design. Cycle 2 must either retain one exact approved company or stop for a separately approved multi-company authority contract.

Permission resolution must be denial-first:

1. authenticated user;
2. approved GL/TB role purpose;
3. exact authorized selected company;
4. Page/Report authority if the selected adapter depends on it;
5. source DocType and field authority;
6. Finance Book, Cost Center, Project and dimension authority;
7. sensitive account-class policy;
8. exact dates/fiscal context and supported filter combination;
9. source-version and consistency contract;
10. bounded query and response validation.

Potentially sensitive account classes include bank/cash, payroll/employee, tax, AR/AP control, intercompany, equity/capital, suspense/temporary, clearing, write-off, provisions, and any sparse custom dimension. C2C4 must classify each as visible aggregate, coarsened/suppressed in optional presentation, separately authorized, or fully unavailable. Display suppression may remove an optional category summary, but it must not remove a ledger account from the internal full-chart invariant. If the user lacks source authority for any required ledger account, the balanced posture is unavailable. The public payload must not allow a user to infer a restricted balance through subtraction, category totals, sparse dimensions, or repeated filters.

## 11. Failure, unavailable, and integrity-exception contract

The exact codes will be frozen in C2C3. The planning taxonomy is:

| Class | Examples | Public behavior |
| --- | --- | --- |
| Unauthorized | guest, wrong role, company denied, report/DocType/field denied | Reject before source read; no financial context or totals. |
| Restricted | authenticated Finance shell role without approved GL/TB purpose or sensitive account scope | Show bounded restricted state with no totals or identities. |
| Unsupported | fiscal context, Finance Book, dimension, currency, hierarchy, PCV option, or installed version not covered | Show controlled unsupported state; no partial totals. |
| Source unavailable | permission-preserving source error, timeout, over-cap result, missing installed source, or safe adapter cannot run | Clear prior data and show unavailable; no zero substitute. |
| Malformed/inconsistent | wrong types, duplicate or orphaned rows, unknown accounts, cross-company data, invalid dates/currencies, hierarchy mismatch, or mixed source versions | Fail closed, clear totals, record internal bounded evidence. |
| Concurrent/stale | source changes during reconstruction, late browser result, authority/context change, route departure or user switch | Discard result, clear prior data, and announce only the current request state. |
| Accounting integrity exception | authoritative bounded result is unbalanced or does not reconcile under the proven contract | C2C decides whether safe aggregate exception evidence may be shown; never label ready/balanced/certified. |

Failure handling must not expose stack traces, SQL, DocType field names, account names, vouchers, parties, users, roles, bank identifiers, tax identifiers, or internal reconciliation keys. Frappe permission messages generated by a denied source read must not leak into the browser.

## 12. Test and evidence matrix

| Evidence family | Minimum cases |
| --- | --- |
| Basic accounting | balanced simple period; multiple debit/credit accounts; opening only; movement only; closing only; zero balances; negative/net cases; exact fixed decimals. |
| Opening/fiscal | new company opening, migration/opening entries, mid-year start, prior-year carry-forward, fiscal boundary, no PCV, one PCV, multiple/late PCVs, unclosed P&L option, later posting. |
| Lifecycle | submitted postings, immutable-ledger cancellation/reversal, amendments, returns/credit/debit effects where they reach GL, disabled/renamed/malformed accounts. |
| Hierarchy | group/ledger rollup, each root type, nested groups, zero groups, cross-company account rejection, hierarchy total equality. |
| Context | allowed/denied company, date boundaries, period status, base currency, precision/rounding, Finance Book default/explicit/exclusion, Cost Center, Project and custom dimensions. |
| Reconciliation | opening + movement = closing; opening/period/closing debit-credit equality; GL-to-TB parity; report-versus-reconstruction parity if evaluated; threshold and unexplained residual rejection. |
| Permission | guest, wrong role, System Manager-only, Accounts User, candidate Manager/Controller/Auditor, mixed roles, missing/ambiguous company, report/DocType/field denial, dimension/account-class denial. |
| Privacy/schema | exact keys/types; forbidden party/voucher/account/bank/tax/payroll/user/role/action/native-route/export fields; sparse-category inference; unknown/nested key rejection. |
| Malformed/caps | null/non-finite/oversized decimal, invalid date/currency, duplicate/orphan/cross-company row, unknown root type, over-cap volume, timeout, partial source, inconsistent source version. |
| Consistency/concurrency | same-snapshot proof or reconstruction token, source mutation between reads, refresh supersession, late success/error, context/authority change, logout/user switch. |
| Browser lifecycle | loading, ready, empty, restricted, unavailable, error and rejected payload; repeated refresh, timeout, supersession, route departure, wrapper hide and return. |
| Accessibility/responsive | semantic headings/landmarks, keyboard/focus, visible focus, persistent polite status, reduced motion, zoom/reflow, text expansion, 1440px/1366px, 1024px/860px, 390px and 320px production renderer. |
| Cross-workspace | Finance isolation always; formal Sales/Procurement and applicable Warehouse/Finance gates when shared/routing/registry/governance triggers exist. |
| Release/live | exact source hashes, cached manifest, source/live allowlist, authenticated allowed and denied role pairs, intentional drift, rollback/recovery; only under separate approvals. |

Source tests and representative smoke prove source behavior only. They never substitute for authenticated live acceptance.

## 13. Ownership locks and likely file surfaces

### 13.1 Current documentation task

Exact candidate allowlist:

1. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/finance-accounting-cycle2-gl-trial-balance-scope-implementation-plan-2026-07-17.md`
2. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/README.md`

The accepted capability map remains read-only and must retain SHA-256 `9c9748a243744c57175d684d1f963e337dacaac5aa36f1faf420d7a92642e2bd` during this documentation outcome.

### 13.2 Future source-proof surfaces

C2A5 must identify exact installed source/report paths and create a separate read-only allowlist. No source-proof task may use the live deployment tree or operational data merely because an installed path is relevant.

### 13.3 Provisional future runtime locks

These are overlap warnings, not an implementation allowlist:

- `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/finance_accounting/service.py`;
- a possible new Finance-owned GL/TB adapter module, only if C2B/C2C justify it;
- `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/erp_workspace_ui/erp_workspace_ui/page/finance_control_desk/finance_control_desk.js` and page metadata;
- Finance backend, browser, resolver, shell, lifecycle, source, responsive and renderer tests/smokes;
- `workspace_registry.py`, browser registry, governance manifest, `boot.py`, hooks/app boot, shared sidebar/runtime and common CSS only if explicitly triggered;
- Sales, Procurement and Warehouse pages/services/tests/smokes only under their owners and only for a separately justified impact.

One writer owns each runtime surface. Main Control freezes the exact implementation manifest before C2D. Parallel research is allowed; parallel writers on the Finance service/page, registry/governance, routing, Shared UI, or protected workspaces are not.

## 14. Main Control orchestration model

Main Control remains the single orchestration and synthesis layer. The Owner is not required to relay routine prompts, findings, or reports between specialists.

Bounded tasks are:

- **Installed-source specialist:** locate and trace exact ERPNext/Frappe report and ledger behavior; no design authority beyond evidence.
- **Accounting-semantics specialist:** validate formulas, lifecycle, PCV/opening/fiscal, book/dimension/currency, hierarchy and reconciliation conclusions.
- **Security/permission specialist:** validate denial-first authority, sensitive account classes, inference risks, payload schema, stale context and no-execution boundary.
- **Shared UI/protected-workspace specialist:** validate premium composition, shared contracts, lifecycle/accessibility/responsiveness and regression triggers.
- **Release/governance specialist:** validate exact manifests, ownership locks, evidence scores, approval separation, live/rollback conditions and closure truth.
- **Main Control:** assigns exact questions and evidence, resolves conflicts, accepts evidence-backed findings, synthesizes once, proposes the next bounded gate and owns final scope adjudication.

Material accounting, security, Shared UI and release risks receive independent counterpart review. Reviews are time-bounded and evidence-based. Repeated open-ended review loops, speculative Blocker/High findings, or broad cleanup requests are rejected.

## 15. Approval gates and stop conditions

### 15.1 Sequential approval gates

1. Plan/scope acceptance.
2. C2B installed-source proof authorization.
3. C2B source-proof closure and C2C contract authorization.
4. C2C design acceptance and exact C2D runtime authorization.
5. Source acceptance.
6. Staging approval.
7. Commit approval.
8. Push approval.
9. Live-alignment approval.
10. Required operational-action approval, if any; none is currently expected.
11. Authenticated live-acceptance approval.
12. Cycle 2 closure acceptance.

No gate implies the next.

### 15.2 Stop conditions

Main Control stops the affected outcome when:

- branch, HEAD/upstream, index, exclusions, source/live boundary or candidate manifest is unclassified;
- installed Trial Balance or GL semantics cannot be proven at the pinned version;
- report execution or reconstruction cannot preserve role, company, source, field, account-class or dimension permissions;
- opening, period, closing, PCV, hierarchy, currency, book or dimension behavior remains materially ambiguous;
- GL-to-TB parity or debit/credit invariants cannot be reconciled within an explicitly approved precision policy;
- a result requires native report passthrough, raw unrestricted query, browser authority, or identity-bearing rows;
- a shared/runtime change would broaden or break a protected workspace without an accepted impact plan;
- a material accounting, security, Shared UI or release Blocker/High is supported by concrete repository/product evidence and remains unresolved;
- required evidence would need unauthorized operational data, execution, metadata, permission, migration, service or live action;
- the proposed outcome expands into statements, close, liquidity, consolidation, AI or execution without a new Owner scope decision.

## 16. Definition of Cycle 2 done

Cycle 2 may close only when all applicable conditions are evidenced:

- exact business outcome and role/company/context contract accepted;
- installed sources and semantics pinned and reproducible;
- opening, movement, closing, hierarchy, PCV, currency, Finance Book and dimension rules proven;
- selected adapter is permission-preserving, bounded, consistent, capped and fail-closed;
- every public value has an accounting invariant and GL/TB reconciliation boundary;
- public schema contains no forbidden identity, row, route, export or action surface;
- premium UI is truthful, accessible, responsive and consistent with shared contracts;
- existing Finance, Sales, Procurement and Warehouse behavior is preserved under the trigger matrix;
- no open evidence-backed Blocker/High remains;
- source, staging, commit, push, live, metadata, permissions, protected gates and browser evidence are truthfully and separately recorded;
- all intentional drift and deferred scope is documented;
- Owner accepts closure and separately decides the next Finance cycle.

Closure of Cycle 2 will not approve statements, close, monetary liquidity, consolidation, Payment Schedule work, bank reconciliation-status work, Finance-to-AI access, or accounting execution.

## 17. Evidence scorecard for plan acceptance

Scale: 0 absent, 1 partial with caveat, 2 complete for this planning outcome.

| Category | Target | Planning evidence/caveat |
| --- | ---: | --- |
| Scope and outcome boundary | 2 | Business result, non-goals, five phases and deferrals explicit. |
| Source/version strategy | 1 | Candidate sources and proof questions exact; installed proof intentionally deferred to C2B. |
| Accounting semantics | 1 | Required questions/invariants complete; installed answers intentionally deferred. |
| Authority/privacy | 1 | Required model and denial sequence defined; Owner roles/account classes unresolved by design. |
| Shared UI/protected impact | 2 | Default no-shared-change rule, premium contract and trigger gates explicit. |
| Tests/evidence | 2 | Required source, accounting, security, lifecycle, responsive and live evidence mapped. |
| Ownership/release containment | 2 | Exact docs allowlist, provisional locks, approvals and stop conditions explicit. |
| Runtime/live validation | N/A | No runtime or live claim is made by the planning outcome. |

No applicable category may be 0. Partial scores are mandatory pre-implementation work, not approval defects for this plan.

## 18. Bounded review findings and disposition

| Severity | Finding | Disposition in this plan |
| --- | --- | --- |
| High future stop gate | Native General Ledger report loads unnecessary party-name identities through a `get_all` path. | Accepted. GL report is proof/reconciliation oracle only and excluded from runtime adapter use. |
| High future stop gate | Native Trial Balance opening, movement, account-tree and dimension paths do not automatically share one proven permission contract when imported by a custom service. | Accepted. C2B proves every path; permission mismatch rejects direct report reuse and favors controlled reconstruction. |
| High future stop gate | Submitted PCV does not prove a completed, unique and reconciled Account Closing Balance cache. | Accepted. Non-completed, incomplete, duplicate or unreconciled cache makes the result unavailable. |
| High future stop gate | Debit-equals-credit can be false for filtered/permission-limited slices even when the complete company ledger is valid. | Accepted. Initial posture is one company, complete chart, base currency, explicit book and no dimension/account/party slice. |
| High future stop gate | A user without complete-chart source authority cannot receive a trustworthy `balanced` result. | Accepted. Return unavailable; never label a visible subset balanced. |
| Medium | Native date clamping, `flt` arithmetic, implicit book handling and unrecorded semantic settings could change the financial context. | Accepted. Strict dates, Decimal precision, explicit book mode and full source/settings fingerprint are mandatory. |
| Medium | Existing Finance roles do not establish Controller/Auditor GL authority. | Accepted. C2A4 Owner decision required; no role or permission change is implied. |
| Medium | A new report route/shared report shell would expand integration and protection risk without business need. | Accepted. Existing Finance workspace-home route and Overview posture are the default. |
| Low | Premium polish could drift into charts, decoration or Cycle 1 cleanup. | Accepted containment. No chart; comparable polish, not visual sameness; Cycle 1 remains unchanged. |

No present documentation Blocker or uncontained High remains after these gates. Installed proof, role decisions, adapter choice, category summaries, runtime implementation and live evidence remain deferred. Rejected shortcuts include native report passthrough, browser aggregation/authority, implicit all-books union, dimension-filtered balance claims, new route/sidebar/search, account/voucher rows, and Shared UI changes by convenience.

## 19. Current planning receipt and next task

Planning result after documentation validation: `planning_baseline_documented`.

The next explicit Owner decision is `finance_cycle2_gl_tb_source_proof_authorized`. Without that exact authority, C2A/C2B do not start.

For this planning outcome:

- source documentation only;
- no Finance Cycle 2 source proof or runtime implementation started;
- no tests, protected gates, staging, commit, push, live access/alignment, restart, cache clear, metadata, migration, permission or accounting action authorized;
- capability map architecture, rankings, boundaries and deferred scope remain unchanged;
- four unrelated exclusions remain untouched.

After Owner acceptance of the exact completed plan, Main Control's next proposal will be a bounded C2A1/C2B1 baseline and installed-source inventory task with its own exact read-only evidence scope. It will not include runtime implementation.
