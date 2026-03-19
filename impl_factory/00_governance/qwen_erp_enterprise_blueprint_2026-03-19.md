# Qwen ERP Assistant Enterprise Blueprint

Date: 2026-03-19
Status: Target Architecture Blueprint
Scope: `Qwen Chat` path inside ERPNext using `Qwen-Agent + FAC MCP + hosted/self-hosted Qwen`

## 1. Purpose

This document defines the target enterprise architecture for the Qwen-based ERP assistant path.

It exists to prevent the project from drifting as a prompt-led prototype and to ensure future development is:

- contract-governed
- tool-grounded
- policy-controlled
- auditable
- multilingual
- safe for enterprise read and write workflows

This blueprint treats `Qwen-Agent` as a bounded reasoning component, not as the system architecture.

## 2. Non-Negotiable Principles

1. ERP/FAC outputs are the only business-fact authority.
2. The model may propose, classify, summarize, and translate; it must not invent ERP facts.
3. Follow-up handling must be resolved from typed context, not keyword patches.
4. All write actions must pass through `propose -> preview -> confirm -> execute -> audit`.
5. Charts, reports, and dashboards must be generated from grounded structured data, not freeform markdown alone.
6. Security, audit, and release governance are first-class architecture layers, not later hardening work.
7. Burmese and English are product requirements, not a prompt trick.

## 3. Product Modes

The target product supports these modes under one governed architecture:

- `read_query`
  Grounded ERP answers from reports, lists, documents, and summaries.
- `follow_up`
  Refine, regroup, project, sort, convert, compare, or continue from a prior grounded turn.
- `artifact_request`
  Generate chart/report/dashboard artifacts from grounded data.
- `write_request`
  Create, update, or delete ERP objects with confirmation and audit.
- `clarification`
  Ask a blocker-only clarification when execution cannot safely continue.

## 4. Enterprise Layer Model

### 4.1 Interaction Layer

Responsibilities:

- ERPNext chat UI
- chat cards for tables, charts, confirmations, and downloads
- language-aware rendering
- session and message timeline

Must not own:

- business truth
- authorization decisions
- write execution
- follow-up semantics

### 4.2 Interaction Contract Layer

Every user turn must be normalized into a typed `InteractionContract`.

Minimum fields:

- `request_id`
- `session_id`
- `user_id`
- `site_name`
- `raw_message`
- `detected_language`
- `ui_channel`
- `received_at`

Purpose:

- separate transport/UI concerns from reasoning concerns
- create a stable envelope for audit and downstream layers

### 4.3 GroundedTurnContext Layer

This is the most important next layer to add.

It stores the last grounded result as structured state, not just message text.

Minimum fields:

- `source_kind`
  report, list, document, search, artifact, write_preview
- `source_name`
  report/tool/capability name
- `grounded`
  true only when backed by successful FAC/ERP result
- `base_language`
- `company`
- `date_range`
- `filters`
- `dimensions`
- `metrics`
- `returned_schema`
- `table_rows`
- `artifact_ids`
- `transform_chain`
- `origin_request_id`
- `trace_request_id`

Purpose:

- make follow-ups resolvable from structure
- keep presentation transforms separate from business-grounded turns
- support audit and replay

### 4.4 FollowUpResolution Layer

Every non-initial turn must be resolved into a typed follow-up class.

Required follow-up classes:

- `presentation_transform`
  example: show in million, respond in Burmese
- `column_projection`
  example: only item name and qty
- `sort_or_limit`
  example: top 5, descending, latest only
- `filter_refinement`
  example: only Yangon, only overdue above 30 days
- `grouping_change`
  example: by territory, by customer, by warehouse
- `metric_change`
  example: value vs qty
- `sibling_switch`
  example: how about receivable after payable
- `artifact_generation`
  example: show as chart, build dashboard
- `write_intent`
  example: create invoice, delete ToDo
- `new_query`
  no reliable dependency on prior grounded context

This layer must operate on:

- current `InteractionContract`
- latest `GroundedTurnContext`
- capability/report registry metadata

It must not operate through one-off string hacks.

### 4.5 Execution Path Layer

After follow-up resolution, the system must choose exactly one path:

- `local_transform`
- `local_projection`
- `erp_requery`
- `artifact_build`
- `write_proposal`
- `clarify`
- `reject`

This decision must be explicit and auditable.

### 4.6 Capability and Report Registry Layer

Maintain a governed registry describing:

- report families
- allowed tools
- required filters
- common follow-up affordances
- output schema
- chartable fields
- write-capable operations
- multilingual business labels

This registry is what allows:

- payable -> receivable style sibling switching
- chart generation from known metrics
- deterministic follow-up resolution

### 4.7 Policy and Authorization Layer

Responsibilities:

- user identity and role scope
- read/write capability boundaries
- confirm-required actions
- destructive action policies
- tool allowlists
- company/site restrictions

This layer must live outside the model and outside the UI.

### 4.8 Tool Gateway Layer

FAC MCP access must be wrapped by a local gateway policy layer.

Responsibilities:

- tool allowlist enforcement
- argument sanitation
- invalid filter recovery where deterministic
- timeout/retry bounds
- service credential isolation
- write prohibition in read mode

### 4.9 Validation Layer

Every final answer must pass typed validation before display.

Checks include:

- grounded answer required for factual claims
- no fabricated totals, IDs, dates, or statuses
- write actions never executed without confirmation state
- language rendering does not alter business facts
- artifact output is derived from grounded schema

### 4.10 Artifact Engine Layer

Charts, downloadable reports, and dashboards must come from structured data.

Artifact types:

- `table_artifact`
- `chart_artifact`
- `dashboard_proposal`
- `export_artifact`

The model may request an artifact, but the backend must build it deterministically.

### 4.11 Language and Locale Layer

This layer owns:

- language detection
- Burmese Unicode normalization
- bilingual glossary mapping
- reply-language policy
- numeric/date formatting by locale

Rules:

- if user asks in Burmese, reply in Burmese
- if user asks in English, reply in English
- business facts remain unchanged across language rendering

### 4.12 Write Safety Layer

All create/update/delete operations must pass through:

1. `intent_detected`
2. `action_proposal_generated`
3. `server_validation`
4. `preview_generated`
5. `user_confirmation`
6. `execution`
7. `post_execution_audit`

Delete actions require stronger policy than create/update.

### 4.13 Audit and Observability Layer

Persist per turn:

- interaction contract
- grounded context snapshot
- follow-up resolution
- execution path
- tool calls
- validation result
- artifact ids
- confirmation state
- language
- security context
- latency
- failure reason

### 4.14 Release Governance Layer

Nothing becomes enterprise-ready without:

- smoke packs
- grounded golden cases
- multilingual tests
- write safety tests
- artifact output tests
- rollback rules

## 5. Core Contract Set

## 5.1 InteractionContract

Purpose:

- stable entry envelope for every user turn

Minimum fields:

```json
{
  "request_id": "uuid",
  "session_id": "string",
  "user_id": "string",
  "site_name": "string",
  "raw_message": "string",
  "detected_language": "en|my|mixed",
  "received_at": "iso-datetime"
}
```

## 5.2 GroundedTurnContextContract

Purpose:

- structured memory of the last grounded business result

Minimum fields:

```json
{
  "grounded": true,
  "source_kind": "report",
  "source_name": "Sales Analytics",
  "company": "Mingalar Mobile Distribution Co., Ltd.",
  "filters": {},
  "dimensions": [],
  "metrics": [],
  "returned_schema": [],
  "table_rows": [],
  "artifact_ids": [],
  "origin_request_id": "uuid",
  "trace_request_id": "uuid",
  "transform_chain": []
}
```

## 5.3 FollowUpResolutionContract

Purpose:

- explicit classification of the current turn relative to prior grounded context

Minimum fields:

```json
{
  "mode": "filter_refinement",
  "depends_on_grounded_turn": true,
  "delta": {},
  "confidence": "high",
  "requires_clarification": false
}
```

## 5.4 ExecutionPathContract

Purpose:

- choose exactly one enterprise path

Minimum fields:

```json
{
  "path": "erp_requery",
  "reason": "territory refinement requires re-running the grounded report",
  "target_capability": "sales_analytics",
  "validation_required": true
}
```

## 5.5 ActionProposalContract

Purpose:

- safe representation of user-requested write actions

Minimum fields:

```json
{
  "action_type": "delete_document",
  "doctype": "ToDo",
  "target_id": "TODO-0001",
  "proposed_changes": {},
  "preview_text": "Delete ToDo TODO-0001",
  "requires_confirmation": true
}
```

## 5.6 ArtifactContract

Purpose:

- structured artifact generation from grounded data

Minimum fields:

```json
{
  "artifact_type": "chart",
  "title": "Monthly Sales Trend",
  "table_schema": [],
  "chart_spec": {},
  "download_formats": ["png"]
}
```

## 5.7 LanguageContract

Purpose:

- stable language behavior

Minimum fields:

```json
{
  "input_language": "my",
  "output_language": "my",
  "glossary_applied": true,
  "translation_mode": "fact_preserving"
}
```

## 5.8 AuditEnvelopeContract

Purpose:

- post hoc proof of what happened

Minimum fields:

- all above contracts
- tool trace
- security scope
- confirmation events
- validation outcome

## 6. Feature Blueprint

## 6.1 Create/Delete with Confirmation

Target behavior:

- user asks for create/delete/update
- system produces `ActionProposalContract`
- UI shows preview card
- user confirms explicitly
- backend validates permissions and payload
- execution occurs through controlled adapter
- result is audited

Requirements:

- no direct model execution
- idempotency keys for writes
- delete policy and stronger confirmation
- least-privilege service identity

## 6.2 Chart / Report / Dashboard / PNG

Target behavior:

- user asks for chart or dashboard
- if prior grounded table exists, build locally
- otherwise run grounded query first
- backend emits structured chart/dashboard artifact
- UI renders chart card
- user can download PNG

Requirements:

- chart engine separated from model
- chart spec generated from schema/metrics
- dashboard creation goes through proposal and save step

## 6.3 Burmese / English

Target behavior:

- Burmese input -> Burmese answer
- English input -> English answer
- bilingual glossary for ERP terms
- no silent meaning drift in translated metrics

Requirements:

- Unicode normalization
- language detection per turn
- glossary registry
- multilingual replay set

## 7. Security Blueprint

Minimum enterprise controls:

- replace Administrator prototype auth with dedicated least-privilege service user
- separate read and write credentials
- scoped tool allowlists by mode
- server-side validation for every write proposal
- audit every tool call and confirmation event
- sanitize rendered HTML/markdown/artifacts
- rate limiting and abuse detection
- secret rotation policy
- network isolation for external model/runtime hosts

## 8. Anti-Patterns To Avoid

Do not build this product by:

- keyword patches for follow-ups
- prompt-only write safety
- letting Qwen-Agent own the architecture
- using markdown as the only artifact format
- storing only freeform transcript without typed context
- using Administrator credentials long-term
- treating Burmese as a UI translation afterthought

## 9. Phased Enterprise Roadmap

## Phase A: Contract Foundation

Deliver:

- `InteractionContract`
- `GroundedTurnContextContract`
- `FollowUpResolutionContract`
- `ExecutionPathContract`

Exit criteria:

- every successful turn stores grounded typed context
- every follow-up records its resolution mode

## Phase B: Follow-Up System

Deliver:

- local transform path
- column projection path
- filter refinement path
- sibling-switch path from registry metadata

Exit criteria:

- follow-ups no longer depend on prompt hacks

## Phase C: Artifact System

Deliver:

- chart artifacts
- report export artifacts
- dashboard proposal/save flow
- PNG download

Exit criteria:

- chart/dashboard requests no longer rely on markdown-only responses

## Phase D: Write Safety

Deliver:

- `ActionProposalContract`
- confirmation cards
- controlled create/update/delete adapters
- destructive-action policy

Exit criteria:

- no write action can bypass confirmation and audit

## Phase E: Multilingual Enterprise UX

Deliver:

- Burmese/English language layer
- glossary registry
- multilingual validation/replay packs

Exit criteria:

- language behavior is stable and fact-preserving

## Phase F: Operational Hardening

Deliver:

- service-user credentials
- observability
- replay packs
- release gates
- rollback rules

Exit criteria:

- production rollout is governable, observable, and reversible

## 10. Immediate Next Implementation Priorities

In order:

1. implement `GroundedTurnContext` persistence from successful read turns
2. implement typed `FollowUpResolution`
3. route follow-ups through `ExecutionPath`
4. add structured `ArtifactContract`
5. replace Administrator with dedicated service user
6. introduce `ActionProposalContract` for writes
7. add Burmese language layer

## 11. Target Outcome

The enterprise product should behave like this:

- Qwen understands the user well
- FAC and ERP remain the factual authority
- contracts and policy control correctness
- follow-ups are typed and reproducible
- writes are safe and confirmable
- charts and dashboards are structured artifacts
- Burmese and English both work as first-class languages
- every turn is auditable

That is the line between a smart prototype and a true enterprise assistant product.
