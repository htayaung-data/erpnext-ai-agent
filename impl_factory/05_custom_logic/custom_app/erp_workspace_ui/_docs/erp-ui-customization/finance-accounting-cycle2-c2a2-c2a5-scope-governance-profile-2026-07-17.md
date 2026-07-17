# Finance & Accounting Cycle 2 C2A2-C2A5 Scope and Governance Profile

**Main Control authority:** Main Control v2

**Parent plan:** [Finance & Accounting Cycle 2 GL / Trial Balance Scope and Implementation Plan](finance-accounting-cycle2-gl-trial-balance-scope-implementation-plan-2026-07-17.md)

**Preceding evidence:** [Finance & Accounting Cycle 2 C2A1/C2B1 Baseline and Installed-Source Inventory](finance-accounting-cycle2-c2a1-c2b1-baseline-installed-source-inventory-2026-07-17.md)

**Owner approval received:** `finance_cycle2_c2a_scope_governance_profile_approved`

**Decision:** `c2a2_c2a5_governance_profile_documented`

**Source baseline at authoring:** `feature/erpnext-ui-design` at `a7e813babebc4d400b861abd588445d712f2a9fc`

**State:** Owner-approved C2A governance profile and documentation-closure candidate; C2B1 remains stopped before exact installed-source fingerprinting

**Date:** 2026-07-17

## 1. Outcome and authority

This document is the canonical C2A2-C2A5 governance record for the Owner-selected GL / Trial Balance source-proof outcome. It turns the parent plan's provisional C2A questions into accepted business-purpose, financial-context, role, data-classification, ownership, sequencing and protection decisions.

The authority chain is:

1. the accepted Main Control v2 transition handoff;
2. the accepted Codex Delivery Operating Model V1 pilot;
3. the accepted Finance Capability Map and Integration Plan;
4. the published GL / Trial Balance five-phase plan;
5. the published C2A1/C2B1 baseline and source inventory;
6. the Owner's later acceptance of the profile recorded here.

Later accepted evidence supersedes older phase labels and planning hypotheses. In particular, the parent plan's statement that source proof had not started was superseded by `finance_cycle2_gl_tb_source_proof_authorized` and the C2A1/C2B1 receipt. The current source repository remains authoritative if any document conflicts with committed behavior.

This acceptance does not authorize installed-container access, operational-data access, C2B2-C2B7, C2C-C2E, runtime implementation, staging, commit, push, live alignment, metadata, permission changes, protected gates, Finance-to-AI access or accounting execution.

## 2. Current mini-phase receipt

| Mini-phase | Current state after Owner decision | Boundary |
| --- | --- | --- |
| C2A1 Baseline and authority | Complete at the published point-in-time receipt. | New mutable facts require fresh evidence. |
| C2A2 Business outcome and materiality | Approved in this profile. | Operational integrity monitoring only; no assurance, close or statements. |
| C2A3 Financial context | Approved as a bounded policy; installed semantics remain subject to C2B proof. | One company, base currency, fiscal-year-to-date, default Finance Book and no dimension slice. |
| C2A4 Role, SoD and data classification | Approved as a future contract constraint. | Accounts Manager is the sole initial viewer-purpose candidate; no permission change is approved. |
| C2A5 Ownership, files, gates and scope closure | Approved in this profile. | Exact read-only fingerprint allowlist and protected-surface locks are frozen. |
| C2B1 Installed source inventory | Repository/tag inventory complete; exact installed fingerprint stopped. | Requires separate `finance_cycle2_gl_tb_installed_source_fingerprint_access_authorized`. |
| C2B2-C2B7 | Not started. | No accounting, permission, adapter or public-contract conclusion is accepted. |
| C2C-C2E | Not started. | No runtime, UI, release or live-acceptance authority exists. |

C2A is substantively complete by Owner decision. Its repository closure remains a documentation-only candidate until this exact record and README entry pass their distinct staging, commit and push gates.

## 3. C2A2 approved business outcome and materiality

### 3.1 Purpose and supported decision

The approved purpose identifier is `operational_trial_balance_integrity_review`.

For one server-authorized company and one exact financial context, the future bounded Finance posture may answer:

- what aggregate opening debit and credit totals the proven source produces;
- what aggregate debit and credit movement the proven source produces for the period;
- what aggregate closing debit and credit totals the proven source produces;
- whether each required equality and opening-plus-movement-to-closing reconciliation is exact under installed ERPNext semantics;
- whether the result is ready for operational review or requires investigation.

The supported management decision is limited to whether an authorized Accounts Manager should continue normal operational review or investigate an integrity exception. The result is not an independent audit opinion, financial-statement certification, fiscal close approval, completeness assertion beyond the proven source contract, or authority to post or correct accounting entries.

### 3.2 Frequency and freshness

| Policy | Approved posture |
| --- | --- |
| Invocation | Manual, on-demand Refresh only. |
| Scheduling | No polling, scheduled refresh, background notification or unattended cache. |
| Freshness | Point-in-time result generated for the accepted request context. |
| Timestamp | Display a server-derived `generated_at` value in the future safe context. |
| Service claim | No real-time or continuously current SLA. |
| Supersession | A later request, context change, authority change, user switch or route departure invalidates an earlier result. |

### 3.3 Exact materiality rule

There is no business-materiality waiver for the integrity control. A result may be described as balanced only when every required residual is exactly zero after the authoritative installed currency precision and quantization rules are applied and every required reconciliation passes.

The exact precision source, rounding path, treatment of malformed precision and equality formulas remain C2B/C2C proof items. Until they are proven, the result is unsupported. No hard-coded tolerance, browser floating-point comparison, configurable threshold or presentation rounding may convert a non-zero residual into a balanced claim.

### 3.4 Integrity-exception visibility

The approved initial exception posture is status-only:

- identify the authorized company and safe financial context;
- identify the affected control at a non-identity-bearing level;
- show `integrity_exception` or equivalent business-facing status;
- clear all financial totals, residual values and prior ready data;
- expose no account, category, voucher, party, employee, bank, tax, user or source-row detail.

C2C must freeze the exact public schema and wording. This C2A decision does not approve an endpoint or payload.

### 3.5 Explicit non-goals

The following are outside this outcome: account/category summaries, ledger or voucher rows, native reports, drilldowns, exports, statements, close/reopen, cash or bank amounts, payment preparation, multi-company, consolidation, dimensions, forecasting, notifications, approvals, actions, AI access and accounting execution. Discovering relevant source fields does not broaden this scope.

## 4. C2A3 approved financial context

The context is server-owned. Browser input cannot select or widen company, Finance Book, currency, dimensions or account scope.

| Context element | Approved value or rule | Authority and fail-closed rule |
| --- | --- | --- |
| Company | `Mingalar Mobile Distribution Co., Ltd.` only. | Use the Finance permission-preserving resolver pattern. Missing, ambiguous, different or multiple authorized company outcomes are unavailable; do not guess or expose a selector. |
| Company currency | `MMK`, confirmed from authoritative company settings. | Base-currency mode only. Missing, different or ambiguous currency is unsupported. |
| As-of date | Explicit ISO date, defaulted from the server date. | Must be valid, non-future and within one resolved fiscal year. Reject rather than clamp invalid or cross-year input. |
| Period start | Start of the authoritative fiscal year containing the as-of date. | Backend-resolved; no browser override and no custom date range initially. |
| Fiscal year | The one authoritative fiscal year containing the accepted dates. | Missing, overlapping or inconsistent fiscal-year authority is unsupported. |
| Period posture | Provisional operational review. | Never label closed, reopened, audited, certified or published. Period-closing effects require C2B proof. |
| Finance Book | One explicit server-resolved `company_default` posture. | No selector. Missing or ambiguous default, and any unproven blank/NULL semantics, are unsupported until installed-source proof resolves them. |
| Currency mode | Company base currency only. | No account, transaction, presentation or converted currency. |
| Account scope | Complete authorized chart for the company. | Any missing account or inconsistent permission across required sources makes the result restricted or unavailable; never compute a visible subset. |
| Dimension mode | `none`, meaning no requested slice over the complete authorized ledger. | It does not mean blank-only Cost Center, Project or custom-dimension values. No dimension identities or filters are exposed. |
| Precision | Installed authoritative company/currency/system precision. | Missing, inconsistent or unproven precision stops the result. |
| Source identity | Exact installed ERPNext/Frappe revisions, dirty state and selected-file hashes. | Required internal evidence before source semantics may be accepted. Filesystem paths and dirty-state detail are not automatically public. |
| Consistency | One proven bounded read/snapshot or a source-change detection contract. | Partial, mixed-version, concurrent or stale reads fail closed and clear prior data. |
| Generated time | Server-derived timestamp for the completed request. | Informational point-in-time freshness only; it is not a real-time guarantee. |

Unsupported context includes multi-company selection, partial charts, root/category slices, account filters, non-default or multiple Finance Books, cross-fiscal-year/custom ranges, future dates, non-base currencies, Cost Center/Project/custom-dimension slices, unknown precision, unproven period-closing treatment, incomplete cache/PCV posture and mixed source versions.

## 5. C2A4 approved role, segregation-of-duties and data classification

### 5.1 Role-purpose matrix

| Identity posture | Initial GL/TB control-view authority | Approved interpretation |
| --- | --- | --- |
| Accounts Manager present | Candidate only, subject to every company, complete-chart, source and public-contract gate. | Operational control owner; not an independent auditor or certifier. |
| Accounts User without Accounts Manager | Restricted. | Cycle 1 page authority does not grant Cycle 2 GL/TB figures. |
| Auditor without Accounts Manager | Restricted initially. | A future assurance/auditor purpose requires a separate authority and segregation design. |
| System Manager without Accounts Manager | Restricted. | System Manager is not an accounting-data bypass. |
| Accounts Manager plus System Manager, Auditor or another role | Evaluate only through the Accounts Manager operational purpose. | Extra roles add no company, account, dimension, data or assurance authority and create no audit claim. |
| Sales, Procurement, Warehouse or other workspace roles | Restricted. | Workspace access does not inherit Finance authority. |
| Guest or unauthenticated user | Restricted. | No Finance context or figures. |
| AI Assistant or model/tool identity | No authority. | Finance-to-AI remains separately prohibited. |

This matrix is a future design constraint, not a role assignment, Page permission, Report permission or User Permission change.

### 5.2 Company and complete-chart authority

An authorized role is necessary but never sufficient. A future result must also prove one identical company and complete authorized chart across every opening, movement, hierarchy, closing/cache, Finance Book, fiscal, precision and dimension source used by the contract.

If any required source, field, account or permission path is unavailable or inconsistent:

- do not compute or display a subset;
- clear earlier totals;
- return a controlled restricted, unsupported or unavailable posture;
- do not reveal which account, field, role or permission caused the denial.

### 5.3 Public and prohibited data classes

| Data class | Initial posture |
| --- | --- |
| Safe authorized context | Company display name, base-currency code, approved dates/fiscal context, default-book posture, no-dimension posture and generated time, subject to C2C schema review. |
| Ready aggregate controls | Opening debit/credit, period debit/credit, closing debit/credit and non-certifying control status only after every source and permission gate passes. |
| Integrity exception | Status and safe context only; totals and residual detail are cleared. |
| Account/category identity | Deferred and absent initially, including account name, number, root type and category summaries. |
| Transaction identity | Prohibited: voucher, party, customer, supplier, employee, journal, payment, bank, tax and row-level data. |
| User/security identity | Prohibited: user identifiers, raw roles, permission internals, denial causes and internal tokens. |
| Technical internals | Prohibited: SQL, stack traces, DocType fields, filesystem paths, secrets, logs and raw source errors. |
| Action/navigation | Prohibited: native route, list/form/report target, export, print, email, notification, mutation or execution controls. |

## 6. C2A5 ownership, exact scope and protection locks

### 6.1 Current documentation allowlist

The exact working-tree candidate is:

1. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/finance-accounting-cycle2-c2a2-c2a5-scope-governance-profile-2026-07-17.md`
2. `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/_docs/erp-ui-customization/README.md`

No other documentation or historical phase label is cleaned up in this outcome.

### 6.2 Frozen installed-source fingerprint allowlist

The next fingerprint candidate is all and only the 69 exact paths published in Sections 6.1 and 6.2 of the preceding C2A1/C2B1 receipt:

- 43 ERPNext paths;
- 26 Frappe paths;
- no wildcard, directory-recursive or discovered-at-runtime expansion.

The referenced receipt has SHA-256 `99a4c8826c8b02ef9c584d6acd6693104d55dfdbb1a7dd8a9e01818c9d6931d8` at source commit `a7e813babebc4d400b861abd588445d712f2a9fc`. Sections 10.1 and 10.3 of that receipt define permitted evidence and prohibited access. Section 10.2 is dependency explanation only; if any described dependency is not already one of the 69 enumerated paths, it requires a new Owner-approved allowlist rather than implicit expansion.

### 6.3 Ownership model

| Responsibility | Bounded owner |
| --- | --- |
| Roadmap truth, phase authority, final scope and stop decisions | Main Control v2 |
| Installed-code fingerprint operation | One separately authorized code-only operator |
| Installed accounting-semantic tracing | One bounded accounting/source specialist per proof family |
| Permission, company, privacy and leakage review | One bounded security specialist |
| Shared UI and protected-workspace impact review | One bounded integration specialist, activated only if a shared surface is proposed |
| Release and governance containment | One bounded release/governance specialist |
| Canonical evidence synthesis | Main Control v2, one synthesis pass |
| Documentation writer | One writer for the exact documentation allowlist |

Main Control creates, coordinates and inspects specialist tasks directly. The Owner is not required to relay routine prompts or reports. Only Owner decisions, external-state access and explicit approval gates are escalated.

### 6.4 Locked surfaces

Until a later exact approval, the following remain locked:

- the live deployment tree `/home/deploy/erp-projects/erpai_project1`;
- the custom Finance service, page, metadata, tests and smoke files;
- Shared UI, common CSS, sidebar, lifecycle and child-page helpers;
- boot routing, hooks, landing precedence and redirects;
- backend/browser registries and governance manifests;
- Sales, Procurement and Warehouse routes, behavior, roles, request isolation and accepted evidence;
- AI Assistant services, report registries, tools, traces and data-access paths;
- roles, permissions, metadata, operational data and every accounting action.

Any proposal touching Shared UI, routing, registries, governance or a protected workspace stops for a separate impact task with exact allowlists, cross-workspace regression evidence and separate live approval.

### 6.5 Required C2B1 fingerprint evidence

If separately authorized, the exact code-only fingerprint must record:

1. source baseline and unchanged exclusions;
2. immutable image ID/digest and its relationship to the installed backend container;
3. installed ERPNext/Frappe versions, roots, Git revisions and dirty state when available;
4. existence, byte length and SHA-256 for every one of the 69 selected paths;
5. exact comparison against the official-tag manifest without treating tag behavior as installed truth;
6. static accounting and permission dependency evidence limited to selected code;
7. confirmation that no database, ORM, report, site data, configuration, secrets, logs or live tree were inspected;
8. post-task no-change evidence and an explicit C2B1 close-or-stop decision.

## 7. Dependency and sequencing model

Major phases remain sequential: `C2A -> C2B -> C2C -> C2D -> C2E`.

1. Publish this C2A governance record through separate staging, commit and push approvals.
2. Obtain `finance_cycle2_gl_tb_installed_source_fingerprint_access_authorized` before entering the installed backend container for code-only evidence.
3. Complete or stop C2B1 based on exact installed provenance and hashes.
4. Only if C2B1 closes without a material mismatch, run bounded C2B2-C2B6 research lanes where dependencies permit. Accounting, permission and release specialists may work in parallel, but writers and overlapping runtime surfaces remain locked.
5. Run one C2B7 synthesis and stop for the distinct C2C contract-design gate.
6. C2C must freeze accounting formulas, permissions, schema, failure behavior and adapter choice before any C2D runtime proposal.
7. C2D runtime, C2E source release and every live-acceptance action require later exact allowlists and approvals.

Parallel research never means parallel phase acceptance. Source proof, contract design, runtime implementation, staging, commit, push, live alignment, metadata, permission, protected-gate and accounting-execution authorities remain distinct.

## 8. Findings and disposition

| Severity | Finding | Disposition |
| --- | --- | --- |
| High stop gate | Exact installed ERPNext/Frappe revisions, dirty state, image digest and selected-file hashes are not proven by source-repository evidence. | C2B1 remains stopped before installed fingerprinting. |
| High future gate | Identical company/account authority is not yet proven across opening, movement, hierarchy, closing/cache, Finance Book and dimension sources. | Require installed static proof and later permission-contract proof; fail closed on any mismatch. |
| High future gate | Committed AI Assistant company resolution, report/row authority and trace retention are broader and incompatible with this Finance boundary. | Finance-to-AI remains prohibited; no integration proposal proceeds. |
| Medium resolved for C2A | Viewer purpose and segregation semantics were provisional. | Accounts Manager is accepted only as the initial operational-purpose candidate; no independent assurance claim. |
| Medium deferred | Default/blank Finance Book, fiscal closing, precision, consistency and PCV/cache semantics are not proven. | C2B must prove them from exact installed source or mark the context unsupported. |

No current repository Blocker contradicts the approved C2A profile. High findings remain evidence-backed stop gates for later access or exposure; they are not permission to infer semantics from field names or official tags.

Accepted for the bounded profile: one company, base currency, fiscal-year-to-date, manual Refresh, point-in-time freshness, exact-zero integrity, Accounts Manager operational purpose, complete-chart authority, default Finance Book, no dimension slice, aggregate-only ready posture and status-only exception posture.

Not selected for the bounded profile: materiality tolerances, Accounts User/Auditor/System Manager standalone access, multi-company, category summaries, custom ranges, non-base currency, dimension slicing, rows, exports, native navigation, actions and AI access.

Deferred to later proof or approval: exact installed formulas and sources, default/blank Finance Book semantics, PCV/closing behavior, public payload keys, adapter selection, runtime files, Shared UI impact, release/live evidence and every execution capability.

## 9. Closure conditions and next Owner decision

The Owner has accepted the C2A2-C2A5 policy decisions recorded here. C2A documentation closure requires only the controlled publication of this exact document and README entry; staging, commit and push remain separate gates.

The next substantive Owner gate is:

`finance_cycle2_gl_tb_installed_source_fingerprint_access_authorized`

That gate, if granted, authorizes only read-only code provenance and selected-file fingerprinting inside the installed backend container under the 69-path allowlist. It does not authorize the live deployment tree, site/database/report access, operational data, logs, secrets, runtime changes, service actions, C2B2+, protected gates or accounting execution.

If the fingerprint reveals a dirty app, unknown provenance, selected-file mismatch, missing dependency or evidence that cannot be obtained within the allowlist, C2B1 stays stopped and Main Control returns the exact gap for Owner adjudication.

## 10. Documentation receipt and unchanged exclusions

At authoring, the capability-map SHA-256 remains `9c9748a243744c57175d684d1f963e337dacaac5aa36f1faf420d7a92642e2bd`, the five-phase plan SHA-256 remains `5081302170ce7657b93c8ba9a8e98dc5bcf65057d329c2b591ebc21a39e5de28`, and the published preceding receipt SHA-256 remains `99a4c8826c8b02ef9c584d6acd6693104d55dfdbb1a7dd8a9e01818c9d6931d8`.

The four unrelated exclusions remain outside the candidate:

| Path | Required status and SHA-256 |
| --- | --- |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py` | Modified, unstaged; `01668e175610d9d090ea51018badbde8b021103afe13ed878782a58b8ce3b224` |
| `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/browser_supplier_payables_fixture_diagnostic.py` | Untracked; `d9822184b26f3c1ebaf5b93663b1f6c3a495b6482f013092d955748dfdf963c5` |
| `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/ui_smoke/sales_final_acceptance_audit.js` | Untracked; `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `impl_factory/05_custom_logic/custom_app/erp_workspace_ui/a.out` | Untracked; `0063411e61152850243132aa87ef12844a8724adb671bf4f38793bcd2b1ce339` |

No runtime code, test, smoke, registry, manifest, route, Shared UI, protected workspace, AI Assistant, live tree, operational data, role or permission is changed by this documentation outcome.
