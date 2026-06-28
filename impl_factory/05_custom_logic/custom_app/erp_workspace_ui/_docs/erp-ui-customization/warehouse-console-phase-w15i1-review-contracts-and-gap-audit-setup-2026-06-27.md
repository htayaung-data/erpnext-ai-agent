# Warehouse Console Phase W15I1 Review Contracts And Gap Audit Setup

Decision: `docs_only_ready_for_control_review`

Date: 2026-06-27

Scope: documentation only. W15I1 creates strict review contracts for Hardening, Security/Stability, and Operations review of the W15 Warehouse operations implementation. It does not implement runtime UI, backend methods, DocTypes, tests, smokes, live files, route behavior, native ERPNext links, stock documents, stock mutation, Sales runtime, Procurement runtime, notification behavior, commits, pushes, live alignment, restarts, or protected gates.

## 1. Purpose

W15I1 exists because the W15 Warehouse work is no longer just read-only planning. W15E, W15F, W15G, and W15H introduced safe custom-record foundations, backend write methods, manager posture methods, request-only handoff methods, metadata, tests, and inert overview shells. Those foundations are intentionally bounded, but they are still real implementation surfaces.

The next safe move is not to close Warehouse and not to activate every planned workflow. The next safe move is to review the current implementation against strict contracts, produce a gap matrix, patch obvious safe gaps, and only then choose the next active planned workflow lane.

W15I1 defines those contracts.

W15J release closure remains blocked until W15I1 produces the gap matrix, required W15I hardening patches are accepted, independent review agents accept the result, and owner/manual checks are complete.

## 2. Project Background

The ERP Workspace UI project customizes ERPNext workspace experiences with premium role-specific consoles. Sales and Procurement workspaces are protected. Warehouse is the active operations workspace.

Warehouse Console history:

- W1-W3 established Warehouse route planning and protected read-only foundation.
- W4-W8C added read-only inbound, outbound, stock exception, stock posture, movement, and transfer visibility routes.
- W9-W12 organized and polished the read-only Warehouse cockpit and review pages.
- W13-W14 defined premium visual standards and functional scope governance.
- W15A defined the operations blueprint for controlled Warehouse workflows.
- W15C/W15D documented inbound receiving and outbound dispatch policy boundaries.
- W15E built customer return intake foundations: custom records, manager posture, Sales/Admin handoff policy, and request-only handoff behavior.
- W15F built supplier return candidate foundations: custom records, manager posture, Procurement/Admin handoff policy, and request-only handoff behavior.
- W15G built internal transfer candidate foundations: custom records, manager posture, Inventory/Admin handoff policy, request-only handoff behavior, Stock Entry draft policy, overview shell, and closure.
- W15H built cycle count / inventory variance foundations: custom records, draft task backend, manager posture, Inventory/Admin handoff policy, request-only handoff behavior, Stock Reconciliation draft policy, overview shell, and closure.
- W15I is the role, permission, audit, and hardening governance checkpoint.

Current accepted implementation posture:

- Warehouse may capture custom internal evidence records where explicitly approved.
- Warehouse managers may save custom manager posture records where explicitly approved.
- Warehouse managers may request downstream review through custom handoff request records where explicitly approved.
- ERPNext stock/accounting/customer/supplier documents remain blocked.
- Planned Overview shells remain inert unless a later implementation phase explicitly activates them.

## 3. Hybrid Review Ladder

W15I1 uses the Hybrid Review Ladder.

Subagents inside Main Control may be used for:

- First-pass contract checks.
- Mechanical verification.
- Static scan preflight.
- Test coverage review.
- Prompt/contract consistency review.
- Low-to-medium risk implementation review.

Separate review agents remain required for:

- Major phase acceptance.
- Backend write methods.
- Role or permission changes.
- Security-sensitive behavior.
- Business ownership decisions.
- ERPNext document policy.
- Native route exposure.
- Valuation/accounting/commercial exposure.
- Notification/email/portal/external action behavior.
- Live alignment, protected gates, release closure, or commit/push decisions.

Subagent review can reduce commute time, but it does not replace independent acceptance for major changes.

## 4. Shared Review Packet Required For Every W15I Batch

Every W15I audit or patch batch must provide reviewers with:

- Phase id and short description.
- Exact changed files.
- Intended scope.
- Explicit out-of-scope boundaries.
- Relevant service methods, DocTypes, tests, smokes, docs, and UI shells.
- Validation commands run and results.
- Static scan summary.
- Final git status.
- Generated cache cleanup status.
- Boundary confirmation.

If any of these are missing, reviewers should return `rejected_needs_context`.

## 5. Shared Non-Negotiable Boundaries

No W15I batch may introduce or approve:

- Purchase Receipt create/save/submit/cancel/amend/delete.
- Delivery Note create/save/submit/cancel/amend/delete.
- Pick List create/save/submit/cancel/amend/delete.
- Sales Return create/save/submit/cancel/amend/delete.
- Credit Note create/save/submit/cancel/amend/delete.
- Return Delivery Note behavior.
- Purchase Invoice return or debit note behavior.
- Stock Entry create/save/submit/cancel/amend/delete.
- Stock Reconciliation create/save/submit/cancel/amend/delete.
- Stock Ledger mutation.
- Stock Balance mutation.
- Stock Reservation, reserve, or unreserve behavior.
- Stock movement, stock posting, stock increase, or stock decrease.
- Customer notification, email, portal, communication, or external action.
- Supplier notification, email, portal, communication, or external action.
- Native ERPNext route exposure.
- Valuation/accounting/commercial exposure.
- Sales runtime changes.
- Procurement runtime changes.
- Global Quick Find expansion into Warehouse planned workflow actions.
- Unreviewed attachments, files, images, HTML, or portal-visible records.

These remain blocked unless a later owner/security-approved phase explicitly opens one narrowly scoped behavior with its own contract.

## 6. Shared File And Git Discipline

Reviewers must protect the dirty worktree.

Required discipline:

- Do not touch unrelated dirty files.
- Do not revert user or unrelated agent changes.
- Do not run destructive Git commands.
- Do not commit, push, live-align, restart, or run protected gates unless Main Control explicitly asks.
- Report final `git status --short --branch`.
- Identify generated `__pycache__` / `.pyc` artifacts and remove only those created by validation under changed paths.

Known unrelated dirty paths to avoid unless explicitly included:

- `../ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py`
- `../ai_assistant_ui/ai_assistant_ui/qwen_chat/browser_supplier_payables_fixture_diagnostic.py`
- `ui_smoke/sales_final_acceptance_audit.js`

## 7. Hardening Review Contract

### 7.1 Role

Hardening reviews implementation correctness, test coverage, idempotency, validation logic, edge cases, static scans, dirty-scope hygiene, and regression risk.

Hardening is not responsible for business ownership acceptance. Hardening may still flag a business ambiguity when it creates technical risk.

### 7.2 Inputs To Inspect

Hardening must inspect:

- Focused service diff.
- Focused test diff.
- Custom DocType JSON diff when metadata changes.
- UI JavaScript diff when visible shells or controls change.
- Smoke diff when selectors or UI guardrails change.
- Relevant policy docs when behavior depends on policy.
- Existing analogous patterns from previous W15 tracks when useful.

Hardening should not rely only on the author summary if source is available.

### 7.3 Required Checks For Backend Write Methods

Hardening must verify:

- Role gate is server-side and runs before mutation.
- Denied roles are covered by tests.
- Required request id is enforced.
- Same request and same payload returns idempotently where intended.
- Same request with changed payload rejects.
- Cross-source request id reuse rejects.
- Original draft request id cannot be reused for manager or handoff action unless explicitly allowed.
- Source record exists and has allowed status.
- Final or non-ready statuses reject further mutation.
- Actor is session-derived, not client-supplied.
- Source warehouse and target warehouse are visible to the session.
- Line ownership matches the source record.
- Lines are derived from trusted source records for handoff methods.
- Client-supplied arbitrary line rows are rejected where lines must be derived.
- Duplicate line identity rejects where duplicates are unsafe.
- Maximum line count is enforced where relevant.
- Quantity rules match workflow semantics.
- Evidence or note is required for exception states.
- Unknown non-empty top-level fields reject.
- Unknown non-empty line fields reject.
- Forbidden stock, commercial, native route, notification, Sales, and Procurement fields reject.
- Response side-effect flags are false for blocked behavior.
- Valuation payload remains hidden.
- Custom event rows are appended where the workflow contract requires an audit trail.
- Event rows include source references, old/new state, session-derived actor, role family, timestamp, client request id, payload hash, validation result, and note/evidence summary where applicable.
- Event rows remain custom child records only and do not create ERPNext Comment, Communication, Timeline, ToDo, File, Notification, email, or portal-visible records.
- Error messages are clear enough for test assertions and support debugging without exposing sensitive data.

### 7.4 Required Checks For DocType Metadata

Hardening must verify:

- DocTypes are under module `ERP Workspace UI`.
- `is_submittable` is `0`.
- `index_web_pages_for_search` is `0`.
- `actions` is empty.
- `links` is empty.
- Child tables are `istable: 1`.
- Child tables have no direct permissions.
- Parent permissions match the phase policy.
- All fields are read-only unless the phase explicitly approves native form editing.
- No forbidden field types exist.
- Table fields point to the intended child DocTypes.
- Handoff type or decision option lists match policy exactly.
- No native route, URL, file, attachment, email, portal, stock document, valuation, accounting, or commercial fields are introduced.

Forbidden field types:

- `Link`
- `Dynamic Link`
- `Attach`
- `Attach Image`
- `HTML`
- `Button`
- `Currency`

### 7.5 Required Checks For UI Shells And Smokes

Hardening must verify:

- Planned controls are inert.
- No shell-local `<button>`, `<a>`, `[role=button]`, click handler, `frappe.call`, or `frappe.set_route` is added for unapproved behavior.
- CSS selectors are Warehouse-scoped.
- Smoke selectors are stable and scoped.
- Smoke asserts shell count.
- Smoke asserts zero active controls inside planned shells.
- Smoke asserts guardrail copy.
- Smoke asserts native route absence.
- UI syntax passes `node --check` when JS changes.

### 7.6 Required Validation Commands

Hardening should run only the validation relevant to the changed scope:

- `git diff --check HEAD`
- `python3 -m compileall -q erp_workspace_ui` when Python changes or tests run.
- `PYTHONPATH=. python3 -m unittest discover -s erp_workspace_ui/tests -p 'test_*.py'` when service, DocType, or contract tests change.
- `python3 -m json.tool` for changed DocType JSON files.
- `node --check erp_workspace_ui/public/js/warehouse_console/warehouse_console_page.js` when Warehouse UI JS changes.
- `node --check ui_smoke/warehouse_phase_w9a_cockpit_smoke.js` when Warehouse smoke changes.
- Trailing whitespace check for changed docs.

If a validation command is skipped, Hardening must say why.

### 7.7 Hardening Decision Output

Hardening must return:

- `accepted_no_patch`
- `accepted_with_patch`
- `rejected_pending_patch`
- `rejected_needs_context`

Output must include:

- Findings by severity: Blocker, High, Medium, Low.
- Fixes made.
- Validation performed.
- Static scan summary.
- Final git status.
- Boundary confirmation.

## 8. Security/Stability Review Contract

### 8.1 Role

Security/Stability reviews permissions, data exposure, mutation boundaries, native route exposure, dangerous field types, idempotency abuse, external side effects, and stability risk.

Security/Stability is allowed to reject even when tests pass if the behavior expands trust boundaries, exposes native ERPNext surfaces, or creates ambiguous mutation authority.

### 8.2 Inputs To Inspect

Security/Stability must inspect:

- Focused service methods.
- Whitelist/export exposure if present.
- Permission gates and role helpers.
- DocType metadata.
- Response payload fields.
- UI route/link/control changes.
- Smoke negative assertions.
- Tests for denied roles, forbidden fields, idempotency, native route absence, and no-effect flags.
- Relevant policy docs.

### 8.3 Required Security Checks

Security/Stability must verify:

- Role gates are server-side, not UI-only.
- Manager-only methods do not allow Warehouse User or Stock User.
- Evidence-capture methods allow Warehouse User / Stock User only when explicitly approved.
- No Sales, Procurement, Accounts, Finance, customer, supplier, guest, portal, or website role gains Warehouse mutation accidentally.
- Request ids cannot be reused across source records.
- Changed payload retry cannot overwrite or fork business state.
- Actor, owner, user, manager, and timestamp values are not trusted from client payload.
- Forbidden fields are rejected at top level and line level.
- No native route string appears in runtime response or shell-local link behavior.
- No route pattern exposes `/app`, `/desk/Form`, `/desk/List`, `/desk/Report`, or `/desk/query-report`.
- No `Link` or `Dynamic Link` fields are introduced without explicit security approval.
- No `Attach`, `Attach Image`, `HTML`, or file/URL field is introduced without explicit attachment security review.
- No email, notification, portal, Communication, ToDo, Comment, File, or external action behavior is introduced.
- No valuation, rate, amount, tax, account, GL, payment, billing, margin, cost, profit, payable, debit, credit, or refund value is exposed.
- No native ERPNext stock/accounting/customer/supplier document is created, saved, submitted, canceled, amended, deleted, enqueued, or mutated.
- No client payload can set stock effect flags to true.
- Safe response flags remain false and are generated server-side.
- Failure modes are safe and do not partially write unsafe records.

### 8.4 Required Stability Checks

Security/Stability must verify:

- Methods are deterministic for same request id and payload.
- Idempotent responses do not leak broader records.
- Cross-source request id lookup cannot return another user's data.
- Missing source records fail closed.
- Stale or final source states fail closed.
- Line derivation cannot include lines outside source ownership.
- Audit/event rows cannot be forged from client-supplied actor, manager, owner, timestamp, role family, or validation-result values.
- Audit/event rows must not write to ERPNext Comment, Communication, Timeline, ToDo, File, Notification, email, portal, or external systems.
- Empty, malformed, negative, or excessive line payloads fail closed.
- Validation does not rely on UI copy or client-only state.
- Tests cover role denial and changed-payload rejection.

### 8.5 Required Security Validation

Security/Stability should run or confirm:

- `git diff --check HEAD`
- Full unit tests for service or metadata changes.
- JSON validation for DocType metadata.
- Static scan for native routes.
- Static scan for stock/accounting/commercial terms and lifecycle verbs.
- Static scan for notification/email/portal/file/attachment terms.
- Dirty boundary check for Sales and Procurement runtime files.
- Cache artifact cleanup check.

### 8.6 Security/Stability Decision Output

Security/Stability must return:

- `accepted_no_patch`
- `accepted_with_patch`
- `rejected_pending_patch`
- `rejected_needs_context`

Output must include:

- Findings by severity.
- Fixes made.
- Residual risks.
- Validation performed.
- Static/security boundary summary.
- Final git status.
- Boundary confirmation.

## 9. Operations Review Contract

### 9.1 Role

Operations reviews ERP business correctness, user meaning, workflow ownership, role responsibilities, terminology, UI comprehension, and whether a Warehouse action implies a business outcome that Warehouse does not own.

Operations is Owner-adjacent but does not replace Owner authority. Owner manual business-usefulness decisions remain Owner authority.

### 9.2 Inputs To Inspect

Operations must inspect:

- User-facing labels and copy.
- Workflow states and decision names.
- Role ownership sections.
- Planned shell cards and detail panels.
- Backend statuses and handoff type names.
- Manager decision rules.
- Handoff policy mapping.
- Future document policy boundaries.
- README roadmap entries when docs change.
- Screenshots or manual UI observations when provided.

### 9.3 Required Business Ownership Checks

Operations must verify:

- Warehouse owns physical evidence, count, condition, posture, and internal recommendation only.
- Warehouse Manager owns internal review and request-only handoff only.
- Inventory/Admin owns stock document governance and adjustment policy.
- Sales owns customer authorization, communication, replacement, rejection, refund decision, and customer-facing promises.
- Procurement owns supplier communication, supplier authorization, claim, replacement/credit negotiation, and PO correction.
- Finance/Admin owns credit, debit, refund, payable adjustment, write-off, accounting, GL, and document governance.
- Warehouse does not decide customer refund, supplier credit, stock posting, accounting adjustment, or ERPNext document submission.

### 9.4 Required Workflow Meaning Checks

Operations must verify:

- Labels use `candidate`, `request`, `review`, `posture`, `evidence`, or `handoff` where behavior is not execution.
- Labels avoid `approve transfer`, `post stock`, `receive stock`, `issue credit`, `refund`, `notify supplier`, `notify customer`, or similar execution language unless that behavior is explicitly approved.
- `accepted_for_intake_qty` style wording remains distinct from stock acceptance.
- `restock candidate` remains recommendation language.
- `supplier return candidate` is not shortened to `supplier return` when no supplier return is approved.
- `transfer candidate` is not shortened to `transfer` when no stock moves.
- `clean count` does not imply stock adjustment.
- `Inventory/Admin review requested` does not imply Stock Reconciliation draft creation.
- Raw enum keys are not shown to owner-facing UI users.
- Future UI phrases include `request only`, `no document created`, or `no stock moved` where needed.

### 9.5 Required UI/Manual Review Checks

Operations must verify:

- Overview shell remains readable and not overloaded.
- Expand/collapse behavior is understandable.
- Detail panel placement is visually coherent.
- Planned shells clearly read as future or request-only lanes.
- No planned shell looks like an active execution queue unless backend action is approved.
- Owner can understand what to check manually.
- Negative expectations are explicit: no document, no stock movement, no notification, no native route.

### 9.6 Required Operational Risk Checks

Operations must flag:

- Ambiguous ownership.
- Labels that imply stock movement or document approval.
- Workflows that skip manager or Inventory/Admin governance.
- Handoff types that sound like credit/debit/refund/document approval.
- Missing note/evidence requirement for exception decisions.
- Source states that allow manager decisions too early without UI explanation.
- Queue or shell design that hides blocked policy too deeply.
- Any future phase that tries to activate too many planned workflows at once.

### 9.7 Operations Decision Output

Operations must return:

- `accepted_no_patch`
- `accepted_with_patch`
- `rejected_pending_patch`
- `rejected_needs_context`

Output must include:

- Findings by severity.
- Fixes made.
- Operational assessment.
- Role/business ownership assessment.
- Recommended wording or sequencing improvements.
- Validation or inspection performed.
- Final git status.
- Boundary confirmation.

## 10. W15I Gap Matrix Requirements

The next audit phase must produce a matrix with at least these columns:

- Track.
- Phase/source.
- Artifact type.
- Current implementation.
- Required contract.
- Gap.
- Severity.
- Patch recommendation.
- Reviewer required.
- Owner manual check required.
- Boundary risk.

Tracks to include:

- Customer return intake draft.
- Customer return manager decision.
- Customer return Sales/Admin handoff.
- Supplier return candidate draft.
- Supplier return manager decision.
- Supplier return Procurement/Admin handoff.
- Internal transfer candidate draft.
- Internal transfer manager decision.
- Internal transfer Inventory/Admin handoff.
- Cycle count task draft.
- Cycle count manager decision.
- Inventory variance Inventory/Admin handoff.
- Warehouse Overview planned workflow shells.
- W15 policy docs and README roadmap entries.

Artifact types to include:

- Service method.
- Helper method.
- Custom DocType metadata.
- Audit/event record.
- Unit tests.
- UI shell.
- Smoke test.
- Policy doc.
- README entry.

## 11. Severity Definitions

Blocker:

- Unsafe mutation or missing role gate.
- ERPNext stock/accounting/customer/supplier document behavior introduced without approval.
- Native ERPNext route exposure for blocked documents.
- Valuation/accounting/commercial exposure.
- Customer or supplier notification behavior.
- Data leakage across source records or users.

High:

- Idempotency failure.
- Changed payload reuse accepted.
- Cross-source request id reuse accepted.
- Forbidden top-level or line fields accepted.
- Manager-only action allowed to non-manager role.
- Clean/safe state accepts exception lines.
- Handoff lines trusted from client when they must be source-derived.

Medium:

- Missing edge-case test for important validation.
- Ambiguous status gate.
- Missing evidence/note requirement for an exception decision.
- Metadata permission mismatch that does not immediately expose mutation.
- UI wording implies execution but controls are inert.

Low:

- Wording improvement.
- Minor validation message clarity.
- Future UI label suggestion.
- Documentation gap that does not affect current implementation.

## 12. Copy/Paste Prompt For Hardening Agent

```text
Recommended thinking: High. Reason: W15I1 hardening contract review governs backend validation, idempotency, tests, static scans, and gap severity for implemented Warehouse write foundations.

Review W15I1 Hardening contract and the current W15I1 docs-only package.

Files:
- _docs/erp-ui-customization/README.md
- _docs/erp-ui-customization/warehouse-console-phase-w15i-role-permission-audit-hardening-governance-2026-06-26.md
- _docs/erp-ui-customization/warehouse-console-phase-w15i1-review-contracts-and-gap-audit-setup-2026-06-27.md

Scope:
- Docs-only review-contract setup.
- No runtime/backend/DocType/test/smoke/live implementation is approved.
- Verify the Hardening contract is complete enough to audit W15E/F/G/H service methods, metadata, tests, UI shells, and smokes.

Pay special attention to:
- Role denial tests.
- Request-id idempotency.
- Changed-payload rejection.
- Cross-source reuse rejection.
- Source-state gates.
- Forbidden top-level and line fields.
- Derived handoff lines.
- Quantity and evidence validation.
- No-effect response flags.
- Validation command expectations.
- Dirty worktree discipline.

Return:
- Acceptance decision.
- Findings by severity.
- Missing hardening checks, if any.
- Validation performed.
- Static/document scan summary.
- Final git status.
- Boundary confirmation.
```

## 13. Copy/Paste Prompt For Security/Stability Agent

```text
Recommended thinking: High. Reason: W15I1 security contract review governs permission boundaries, native-route containment, data exposure, external side effects, and ERPNext mutation blocking.

Review W15I1 Security/Stability contract and the current W15I1 docs-only package.

Files:
- _docs/erp-ui-customization/README.md
- _docs/erp-ui-customization/warehouse-console-phase-w15i-role-permission-audit-hardening-governance-2026-06-26.md
- _docs/erp-ui-customization/warehouse-console-phase-w15i1-review-contracts-and-gap-audit-setup-2026-06-27.md

Scope:
- Docs-only review-contract setup.
- No runtime/backend/DocType/test/smoke/live implementation is approved.
- Verify the Security/Stability contract is strict enough for W15E/F/G/H custom-record write foundations and future gap audit.

Pay special attention to:
- Server-side role gates.
- Permission boundary by role family.
- Native route patterns.
- Forbidden field types.
- Attachment/file/email/portal risks.
- Stock/accounting/customer/supplier document lifecycle blocking.
- Valuation/accounting/commercial exposure blocking.
- Idempotency abuse and cross-source data leakage.
- Notification/customer/supplier external action blocking.
- Dirty Sales/Procurement runtime boundary.

Return:
- Acceptance decision.
- Findings by severity.
- Residual risks.
- Missing security checks, if any.
- Validation performed.
- Static/security boundary summary.
- Final git status.
- Boundary confirmation.
```

## 14. Copy/Paste Prompt For Operations Reviewer

```text
Recommended thinking: High. Reason: W15I1 operations contract review governs ERP business ownership, workflow terminology, planned-shell meaning, and safe sequencing before activating planned workflows.

Review W15I1 Operations contract and the current W15I1 docs-only package.

Files:
- _docs/erp-ui-customization/README.md
- _docs/erp-ui-customization/warehouse-console-phase-w15i-role-permission-audit-hardening-governance-2026-06-26.md
- _docs/erp-ui-customization/warehouse-console-phase-w15i1-review-contracts-and-gap-audit-setup-2026-06-27.md

Scope:
- Docs-only review-contract setup.
- No runtime/backend/DocType/test/smoke/live implementation is approved.
- Verify the Operations contract is strict enough to audit W15E/F/G/H business meaning, ownership, labels, planned shells, and next-lane sequencing.

Pay special attention to:
- Warehouse vs Warehouse Manager vs Inventory/Admin vs Sales vs Procurement vs Finance/Admin ownership.
- Candidate/request/posture wording.
- Avoiding execution wording for blocked ERP document behavior.
- Planned shell manual review expectations.
- Handoff type labels and request-only context.
- Sequencing: W15I1 gap audit first, then one active planned workflow lane at a time.
- Owner manual business-usefulness authority.

Return:
- Acceptance decision.
- Findings by severity.
- Operational assessment.
- Role/business ownership assessment.
- Missing operations checks, if any.
- Recommended wording or sequencing changes.
- Validation or inspection performed.
- Final git status.
- Boundary confirmation.
```

## 15. Boundary Confirmation

W15I1 is documentation only. It introduces no runtime/backend method, DocType metadata, test, smoke, live file, commit, push, live alignment, restart, protected gate, ERPNext stock document behavior, stock mutation, native route exposure, valuation/accounting/commercial exposure, Sales runtime, Procurement runtime, notification/email/portal behavior, or external action.

W15J release closure remains blocked until W15I1 gap audit, required W15I hardening patches, independent review-agent acceptance, and owner/manual checks are complete.
