# Codex Delivery Operating Model V1 Pilot

Date: 2026-07-16

Status: Proposed official pilot for Owner/Main Control approval. This document changes delivery governance only. It does not approve a Finance capability, runtime implementation, live alignment, migration, metadata change, permission change, commit, push, protected gate, or accounting execution.

## 1. Purpose

This operating model adapts the ERP workspace program to current Codex task coordination, stronger frontier models, parallel read-only review, and repository-grounded evidence. It preserves the controls that made Sales, Procurement, Warehouse, and Finance Cycle 1 safe while removing unnecessary prompt relays and single-slice ceremony.

The priorities are, in order:

1. Accounting and operational correctness.
2. Permission, privacy, and execution safety.
3. Protection of accepted workspaces and shared UI contracts.
4. Reproducible evidence and source/live traceability.
5. Delivery speed through bounded parallelism and outcome grouping.

Speed is accepted only when it does not weaken the first four priorities.

## 2. Authority Model

Governance authority and technical truth are separate. Neither can silently override the other.

Governance authority, in order:

1. Owner explicit decision in the current approved task.
2. Accepted outcome charter and current decision log.
3. Accepted closure, freeze, governance, and protection documents.
4. Historical task summaries and conversational context.

Technical truth, in order:

1. Current installed ERPNext/Frappe source, deployed metadata, and actual permission model.
2. Current source repository and committed code at a full commit hash.
3. Fresh validation evidence from the exact candidate package.
4. Source/live checksum evidence from the exact approved allowlist.
5. Historical technical claims.

The Owner decides business intent, scope, risk acceptance, and whether an external action is authorized. The Owner or Main Control Agent cannot make a false technical or accounting claim true by decision. If governance intent conflicts with current technical truth, stop, record the conflict, and reconcile the charter before work continues.

Conversation history is context, not the system of record. A stale phase label must not override a later accepted closure artifact or commit, and an accepted document must not override contradictory current runtime or validation evidence.

## 3. Core Delivery Roles

### 3.1 Owner/Main Control

The Owner/Main Control selects outcomes, approves boundaries, accepts residual risk, approves external-state actions, and chooses the next capability after planning evidence is complete.

### 3.2 Main Control Agent

The Main Control Agent owns the outcome charter, source-of-truth reconciliation, task decomposition, reviewer integration, stop decisions, exact allowlists, and final recommendation. It does not delegate final judgment.

### 3.3 Writer Agent

One writer owns repository changes for an outcome package. Multiple agents must not edit overlapping files in the same worktree. The writer implements only the frozen charter and records every touched path.

### 3.4 Read-Only Counterpart Reviewers

Reviewers independently inspect bounded concerns such as accounting semantics, security/data leakage, shared UI/cross-workspace regression, tests, accessibility, and release containment. Reviewers remain read-only. Accepted remediation is routed through the sole writer so the reviewed candidate and write authority remain unambiguous.

### 3.5 Live Operator

Only one agent performs an approved live operation. Staging, commit, push, live alignment, restart, cache clear, metadata reload, migration, permission change, protected gate, and execution are separate checkpoints. Even when one Owner instruction authorizes several checkpoints, execute them sequentially, verify the evidence and stop conditions after each, and stop the remaining sequence on any mismatch.

## 4. Task Topology

Use a fresh Codex task for each major outcome. The Main Control task holds the charter and integration decision. Subagents provide bounded evidence inside that task.

Preferred topology:

1. One Main Control outcome task.
2. One writer or local writer path.
3. Two to four independent read-only review tracks when risk justifies them.
4. One integrated remediation pass.
5. One fresh cold counterpart review against the final snapshot.
6. Sequential external-state gates.

Do not create a chain of tasks that merely relay prompts and reports. Do not create multiple writers for the same runtime surface. Do not allow subagents to spawn uncontrolled descendants.

## 5. Outcome Grouping

Phases may be grouped when they share one business outcome, one authority boundary, one source model, and one acceptance gate. Grouping is preferred over one prompt per tiny slice when it improves coherence.

Group phases only when all of the following are true:

- The outcome is explicit and testable.
- The data and permission boundary is stable.
- The candidate paths can be allowlisted.
- Rollback is coherent.
- Review disciplines can evaluate the whole outcome.
- No intermediate external-state action is required.

Keep phases separate when they differ in accounting truth, permission authority, source system, execution risk, live operation, or rollback strategy.

Examples:

- Design inventory, dependency mapping, and candidate scoring may be grouped into one capability-map outcome.
- A read-only aggregate source proof and its test contract may be grouped when no live action is involved.
- Runtime implementation, live alignment, metadata changes, and accounting execution remain distinct evidence gates. Tier 2, Tier 3, protected-workspace, and shared-runtime work must not combine candidate creation with external effects in one unchecked operation.

## 6. Mandatory Work Package Charter

Every implementation or high-risk planning task starts with a frozen charter containing:

- Outcome and non-goals.
- Full source commit hash, branch, and upstream relationship.
- Source and live repository paths.
- Installed ERPNext, Frappe, and custom app versions when relevant.
- Exact candidate paths and explicit exclusions.
- Accepted/protected workspace impact classification.
- Shared UI/runtime impact classification.
- Business owner, roles, company, currency, and date boundary.
- Data sources and source-of-truth claims.
- Visibility, review, and execution boundaries.
- Acceptance criteria and required browser roles.
- Required test and smoke evidence.
- Live alignment, restart, cache, metadata, and migration expectations.
- Rollback method.
- Stop conditions.

If the charter changes materially, stop and re-freeze it before implementation continues.

## 7. Risk Tiers

### Tier 0: Documentation and inventory

No runtime or external-state change. Read-only parallel research is encouraged.

### Tier 1: Read-only runtime

UI, resolver, or aggregate/read-only source behavior with no mutation or native execution. Requires role, company, leakage, lifecycle, and source/live evidence.

### Tier 2: Metadata or controlled custom records

Page metadata, permissions, custom workflow records, or custom business records. Requires explicit authority, audit, rollback, and live-operation approval.

### Tier 3: Accounting, stock, payment, tax, close, or external execution

Posting, submission, payment, reconciliation, stock movement, tax filing, close, notifications, email, portal, or external action. Requires separate architecture, control, segregation-of-duties, idempotency, reconciliation, recovery, and protected-gate design before implementation.

Tier 3 always retains a distinct final go/no-go after code acceptance, source/live parity, control evidence, reconciliation evidence, rollback/recovery proof, segregation-of-duties review, and authenticated validation. It cannot be pre-authorized by an implementation approval.

Risk tier may increase during discovery. It must never be reduced merely to fit an existing plan.

## 8. Standard Outcome Flow

1. Reconcile repository, deployed environment, accepted documents, and unresolved decisions.
2. Freeze the outcome charter and candidate manifest.
3. Run bounded read-only research in parallel where useful.
4. Produce one integrated design or implementation plan.
5. Implement with one writer and exact-path ownership.
6. Validate locally against the complete candidate.
7. Run independent counterpart reviews.
8. Resolve accepted findings and reject unsupported findings with evidence.
9. Complete every source artifact and closure/readiness document intended for the current release checkpoint.
10. Repeat a fresh cold review against that exact final snapshot.
11. Stage only the reviewed snapshot, verify the exact manifest and staged diff, then commit and push only after approval.
12. Perform separately approved live actions sequentially from the accepted commit and verify exact hashes after each checkpoint.
13. Obtain authenticated Owner browser evidence where required.
14. If live or browser evidence requires a code or documentation change, form a new candidate, validate it, repeat cold review, and stage only that newly reviewed snapshot. Never append unreviewed closure changes to an already reviewed stage.

Passing tests does not replace accounting review, browser evidence, source/live parity, or permission review.

## 9. Parallelism Rules

Allowed parallel work:

- Independent source inventory by domain.
- Accounting semantics and data-lineage review.
- Security/data-leakage review.
- Shared UI and accepted/protected-workspace regression review.
- Test-contract and release-manifest review.
- Documentation traceability review.

Disallowed parallel work:

- Multiple writers changing the same module or shared runtime.
- Simultaneous live operations.
- Parallel metadata, permission, migration, or accounting execution changes.
- Reviewers modifying the candidate they are meant to review.
- Separate agents making conflicting architectural decisions.

The Main Control Agent integrates reviewer evidence. Majority vote does not decide accounting truth.

## 10. Model Allocation

Use the strongest reasoning where errors are expensive:

- Main architecture, accounting semantics, security synthesis, final closure: `gpt-5.6-sol` at high, xhigh, or max reasoning.
- Primary writer for complex shared runtime or financial source logic: `gpt-5.6-sol` at high or xhigh reasoning.
- Fresh final accounting/security counterpart: `gpt-5.6-sol` at high or xhigh reasoning.
- Bounded inventory, documentation indexing, static scans, and known test runs: `gpt-5.6-terra` at medium or high reasoning.
- Very fast mechanical checks may use a lower-cost model only when the output is independently verifiable.

If an exact model is unavailable to the task, use the strongest available frontier model that supports the required reasoning level and record the substitution. Model strength does not authorize broader scope. A stronger model should group coherent work and deepen verification, not remove gates.

## 11. Evidence Scorecard

Score each category 0, 1, or 2:

- Scope and candidate manifest.
- Source and version freshness.
- Accounting or operational semantics.
- Role, permission, and company authority.
- Data leakage and execution boundary.
- Automated tests and static scans.
- Metadata/configuration authority and deployed verification.
- Source/live parity.
- Accepted/protected workspace and shared UI regression.
- Actual authenticated browser behavior.
- Segregation of duties and approval controls.
- Idempotency and duplicate handling.
- Reconciliation and control totals.
- Audit, retention, and observability.
- Release containment, rollback, and recovery.

Score meaning:

- 0: missing, contradictory, or synthetic-only where actual evidence is required.
- 1: partial, indirect, or accepted with a documented caveat.
- 2: directly verified on the exact candidate or deployed state.

Each score must name evidence IDs or file references, the scorer, rationale, and any caveat. Main Control owns the scorecard; a fresh release or risk reviewer confirms it against the final candidate.

`N/A` is allowed only when the category is explicitly outside the outcome and the package makes no claim about it. `N/A` is excluded from the denominator and must include a reason.

Tier-specific critical categories:

- Tier 0: scope/manifest, source freshness, protected-workspace/shared UI impact, and release containment.
- Tier 1: Tier 0 plus accounting or operational semantics, role/permission/company authority, leakage/execution boundary, and tests/static scans. Source/live parity and authenticated browser behavior become critical when live alignment or live closure is claimed.
- Tier 2: every applicable Tier 1 category plus metadata authority, audit, rollback, and deployed verification.
- Tier 3: every applicable category, including segregation of duties, idempotency, reconciliation, recovery, live parity, authenticated browser evidence, and execution controls.

For acceptance, every critical category must score 2, no applicable category may score 0, and the average of applicable categories must be at least 1.5. A high total cannot compensate for a critical failure. A source-only package may mark live parity and authenticated browser evidence `N/A`, but it must not claim live or production acceptance.

## 12. Mandatory Stop Conditions

Stop implementation or closure when any of the following occurs:

- An open Blocker or High finding.
- Baseline, authority, allowlist, or source model changes unexpectedly.
- An unclassified dirty path appears or a classified exclusion changes status/hash without an updated owner receipt.
- Source/live differences exceed the approved manifest.
- A financial or operational claim cannot be proven.
- Synthetic evidence is presented as authenticated or production evidence.
- Reviewers disagree on a safety-critical claim and the conflict is unresolved.
- Partial, stale, contradictory, or malformed financial values can remain visible.
- Frappe permission messages leak into the browser path.
- Scope expands into rows, identities, native surfaces, mutation, or execution without approval.
- The same root cause reappears twice without an architecture-level correction.
- More than one outcome or writer is active in the same mutable surface.

## 13. Accepted and Protected Workspace Protocol

Sales and Procurement retain their formally protected baselines. Warehouse W16H custom workflows and Finance Cycle 1 are accepted closed-scope baselines that must be preserved from regression, but they are not claimed as formally `Protected` under the Frozen Workspace Protection Package Standard until dedicated packages and executable gates are approved. A new capability may reuse shared infrastructure but must not silently reinterpret or rewrite any accepted or protected baseline.

For every change, classify impact as:

- No protected-workspace impact.
- Adapter-only impact in one workspace.
- Shared UI/runtime impact requiring every formal and interim workspace gate.
- Intentional accepted/protected-workspace change requiring separate approval.

Rules:

- Never fix a protected workspace incidentally inside another workspace task.
- Never copy another workspace's business roles, queues, source semantics, or native exceptions by analogy.
- Never broaden shared navigation or dispatch because one workspace needs a shortcut.
- Preserve accepted landing priority, route identity, lifecycle teardown, search authority, active-item behavior, responsive layout, and target governance.
- For changes to shared-core areas listed by the Frozen Workspace Protection Package Standard, run the formal Sales and Procurement gates plus the interim Warehouse and Finance gates, not only the workspace believed to be affected.
- Record a compatibility matrix for any shared runtime delta.

Until Warehouse has a dedicated executable protection gate, its interim source gate is the full Warehouse regression suite, registry/governance tests, governed route/search/active-item checks, and any applicable custom-workflow smoke. A live shared-runtime change additionally requires exact source/live parity and authenticated Warehouse Manager navigation/isolation acceptance.

Until Finance has a dedicated executable protection gate, its interim documentation gate is exact-manifest validation, documentation reference/whitespace/overclaim checks, and proof that no runtime path changed. Its interim runtime source gate is the full Finance test suite, Finance lifecycle smoke, pinned renderer smoke at 1366px/390px/320px, and cross-workspace regression tests. A live shared-runtime change additionally requires exact source/live parity, role diagnostics, and authenticated Accounts Manager/Accounts User browser acceptance.

## 14. Shared UI and Adapter Contract

Shared core owns:

- Page lifecycle and teardown.
- One-shell and no-stacking behavior.
- Sidebar, header, breadcrumb, filter, and command grammar.
- Responsive and accessibility foundations.
- Request, route, workspace, query, token, and generation isolation.
- Target validation and managed dispatch.
- Common ready, restricted, unavailable, error, and stale-state behavior.

Workspace adapters own:

- Domain payloads and business wording.
- Roles and company authority.
- Productized routes and approved actions.
- Accounting or operational source semantics.
- Explicitly approved native exceptions.

Required shared references:

- `shared-core-workspace-adapter-contract-v2.md`
- `shared-component-and-implementation-golden-rule-standard-v1.md`
- `enterprise-shared-ui-component-standard-v1.md`
- `enterprise-shared-ui-component-implementation-contract-v1.md`
- `frozen-workspace-protection-package-standard-v1.md`
- `native-exception-policy-v1.md`
- `multi-workspace-foundation-contract-v1.md`
- Backend and browser workspace registries, governance manifest, boot routing, and shared sidebar runtime.

Register backend and browser identity before exposing a route. Use exactly one managed shell and one active item. Productized targets are preferred; native targets require manifest classification and permission gating.

## 15. Prior Workspace Preservation Requirements

### Sales

Reference the final freeze, frozen protection package, and v2 protection gate. Preserve Sales routes, role landing, productized customer/item/detail/report surfaces, narrowly approved managed/native document behavior, search/AI authority, timers, breadcrumbs, mobile behavior, and one-shell lifecycle.

Do not copy Sales AI, inquiry, queue taxonomy, pricing/stock semantics, or native form enhancements into another workspace. Any shared change must run the Sales protection gate.

### Procurement

Reference the final freeze closure as the later authority. Preserve Purchase-role landing, productized worklists/reports/details, controlled managed forms/reviews, Quick Find preview-before-Open, PO follow-up boundaries, and PDF/preview restrictions.

Do not add raw native escape, send/email, receive, bill, pay, submit, cancel, amend, broad Supplier/Item mutation, or copy Procurement supplier/item semantics into Finance. Warehouse currently owns the accepted custom receipt visibility and workflow-coordination surface only. ERPNext receipt execution ownership is unapproved and must be decided in a later Warehouse phase. Finance accounting and payment authority likewise requires a separately approved future capability.

### Warehouse

Reference W16H custom-workflow closure. Preserve Overview as navigation/status, dedicated custom workflow routes, bounded custom record posture, controlled unsupported states, and protected custom search/recall behavior.

Do not treat W16H as approval for ERP stock execution. Purchase Receipt, Delivery Note, Pick List, Stock Entry, Stock Reconciliation, stock ledger, valuation, reservation, posting, notification, and accounting remain outside that closure. Do not copy Warehouse operational reads, queues, or custom-write semantics into Finance.

### Finance Cycle 1

Reference F6F Cycle 1 closure and commit `aeed243c76832c958a269d3ca2a0a58ce7616097`. Preserve the company-scoped, read-only, identity-free aggregate posture, manager-only financial aggregates, fail-closed source gates, exact payload validation, stale-state clearing, Page ownership, local live-region containment, and no-execution boundary.

Do not infer approval for GL, AP amounts, schedule aging, cash/bank, tax, close, rows, native reports, exports, payments, posting, reconciliation, write-off, email, portal, or accounting execution.

## 16. Source and Live Discipline

- The design/source branch is the implementation authority.
- The live repository is a deployment/integration mirror and may be broadly dirty.
- Never use broad copy, broad add, or broad synchronization.
- Use exact allowlists and pre/post-copy hashes.
- Preserve unrelated dirty files.
- Confirm source and live indexes before and after operations.
- Restart only the required service and clear only the approved site cache when necessary.
- Metadata reload, migration, permission change, protected gate, commit, and push require explicit approval.
- Record rollback inputs before live action.

## 17. Validation Receipt

Every accepted outcome produces a concise receipt containing:

- Decision and remaining severity findings.
- Full commit and upstream status.
- Files changed and exact allowlist.
- Explicit exclusions and unclassified-path count.
- Tests, static scans, browser evidence, and versions.
- Source/live hash comparison.
- Protected-workspace compatibility result.
- Live actions performed or explicitly not performed.
- Residual risks and deferred scope.
- Recommended next gate.

The receipt must distinguish source-ready, staging-ready, live-aligned, browser-accepted, committed, pushed, and closed states.

## 18. Codex Project Configuration Backlog

Do not introduce repository-wide Codex configuration during the first capability-map outcome. After the pilot is accepted, separately review and approve:

- A concise root `AGENTS.md` for repository truth and protected-workspace rules.
- Narrow nested `AGENTS.md` files only where adapter-specific rules differ.
- Project `.codex/config.toml` defaults.
- Custom accounting, security, and release reviewer profiles.
- A Finance capability-map or financial-source-proof skill/runbook.
- Safe hooks or CI checks for allowlists, forbidden APIs, dirty paths, and closure receipts.

Avoid duplicating long documentation inside agent configuration. Configuration should point to authoritative repository documents.

Official Codex references:

- https://learn.chatgpt.com/docs/agent-configuration/subagents.md
- https://learn.chatgpt.com/docs/agent-configuration/agents-md
- https://learn.chatgpt.com/guides/best-practices.md

## 19. Pilot Exit Criteria

The pilot is successful when one post-Cycle-1 Finance planning outcome demonstrates:

- A frozen charter.
- Useful parallel read-only review without duplicate work.
- One integrated source-of-truth artifact.
- No protected-workspace regression.
- Clear evidence scoring and stop decisions.
- Fewer prompt-relay steps than the previous workflow.
- Equal or better accounting, security, test, and release quality.

The first pilot outcome is the Finance Capability Map and Integration Plan. It is not Finance Cycle 2 and must not select or implement the next capability without a later Owner decision.
