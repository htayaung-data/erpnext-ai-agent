# Qwen ERP Phase 4 Fresh Query Compiler Plan (2026-03-22)

Status: in progress  
Scope: enterprise Phase 4 from the Qwen ERP blueprint  
Phase goal: make first-turn business requests compile into governed, validated ERP execution requests before agent execution.

## Consultation Correction

After Phase 4 review with Qwen-Agent guidance, the steering corrections for this phase are:

1. keep the compiler boundary
2. avoid turning interpretation and compilation into separate network services
3. use a closed-set `intent_class`, not free-text intent labels
4. let the model propose ranked report candidates only as advisory inputs
5. keep semantic validation deterministic by default
6. treat compiler logic as a co-located execution layer, not a remote microservice

## 1. Why Phase 4 Exists

The current architecture is strongest on grounded follow-ups that can reuse stored context.

The largest remaining read-path weakness is now first-turn business queries such as:

- `How much payable amount do we have as of now`
- `Analyze payable amount`
- `Top 5 customers by revenue`
- `Show monthly sales trend in all regions`

These requests still fail or drift because:

1. report selection is not deterministic enough
2. required filter completion is not governed enough
3. single-company context is still showing up as a failure burden
4. grounding validation is stronger than semantic intent-to-result validation

Phase 4 exists to correct that boundary.

## 2. Governing Rule

This phase follows the architecture rule:

- `Qwen-Agent proposes`
- `compiler enforces`

Meaning:

- Qwen/Qwen-Agent may interpret business language and propose intent and slots
- deterministic compiler layers choose the executable ERP path

## 3. What Phase 4 Owns

Phase 4 owns:

1. first-turn business request interpretation contract
2. capability resolution
3. compiler-governed report family / report selection
4. required filter completion
5. single-company invariant injection
6. default time/report-date completion
7. clarify vs execute vs reject decision
8. semantic intent-to-result validation

Phase 4 does not own:

1. local follow-up transforms from grounded context
2. chart/dashboard artifact generation
3. write execution
4. multilingual response rendering

## 4. Target Compiler Flow

The target first-turn execution flow should become:

1. ERP receives `InteractionContract`
2. ERP enters a compiler pipeline
3. compiler obtains a model proposal as an internal compilation step:
   - closed-set intent class
   - candidate capability ids
   - extracted slots
   - ranked candidate reports
   - ambiguity markers
4. ERP compiler validates the proposal against governed metadata
5. ERP compiler selects:
   - capability
   - report family / report id
   - completed filters
   - defaults and invariants
6. ERP compiler decides:
   - `execute`
   - `clarify`
   - `reject`
7. if `execute`, runtime receives a typed compiled request instead of relying on free-form report discovery
8. after result returns, semantic intent-to-result validation runs before answer display

Important implementation rule:

- do not build fresh-query interpretation as a separately exposed network endpoint if it can be avoided
- interpretation is a compiler sub-step, not a standalone service boundary

## 5. Phase 4 Core Contracts

### 5.1 FreshQueryInterpretationContract

Purpose:

- represent the model-proposed understanding of a first-turn business request

Minimum fields:

```json
{
  "intent_class": "financial_summary",
  "candidate_capability_ids": ["accounts_payable_read"],
  "candidate_reports": [
    "Accounts Payable Summary"
  ],
  "requested_dimensions": [],
  "requested_metrics": ["outstanding_amount"],
  "requested_time_scope": "as_of_today",
  "requested_presentation": [],
  "extracted_slots": {},
  "ambiguity_flags": [],
  "ambiguity_reason": "",
  "confidence": 0.0
}
```

Design rule:

- `intent_class` must be a closed-set enum governed by metadata and JSON schema
- `candidate_reports` are advisory only and do not grant report-selection authority to the model

### 5.2 FreshQueryCompilerContract

Purpose:

- represent the compiler-governed executable request

Minimum fields:

```json
{
  "capability_id": "accounts_payable_read",
  "selected_report": "Accounts Payable Summary",
  "selected_report_family": "financial_summary",
  "completed_filters": {
    "company": "Mingalar Mobile Distribution Co., Ltd.",
    "report_date": "2026-03-22"
  },
  "requested_dimensions": [],
  "requested_metrics": ["outstanding_amount"],
  "requested_time_scope": "as_of_today",
  "decision": "execute",
  "clarification_required": false,
  "compiler_reason": "single-company payable summary with report-date default applied"
}
```

### 5.2A CompiledQueryRequestContract

Purpose:

- represent the final typed request sent to runtime execution after compiler enforcement

Minimum fields:

```json
{
  "mode": "compiled_read_query",
  "capability_id": "accounts_payable_read",
  "selected_report": "Accounts Payable Summary",
  "filters": {
    "company": "Mingalar Mobile Distribution Co., Ltd.",
    "report_date": "2026-03-22"
  },
  "requested_dimensions": [],
  "requested_metrics": ["outstanding_amount"],
  "response_policy": {
    "analysis_level": "none"
  }
}
```

### 5.3 SemanticIntentValidationContract

Purpose:

- verify that the returned grounded result matches the requested business intent

Minimum fields:

```json
{
  "requested_capability_id": "accounts_payable_read",
  "returned_report": "Accounts Payable Summary",
  "expected_semantic_tags": ["financial", "payable", "outstanding_amount"],
  "observed_semantic_tags": ["financial", "payable", "outstanding_amount"],
  "time_scope_match": true,
  "dimension_match": true,
  "decision": "pass"
}
```

## 6. Metadata Inputs Required

Phase 4 depends on governed metadata, not phrase-specific logic.

Required metadata inputs:

1. capability registry
   - capability ids
   - closed-set intent classes
   - allowed report families
   - default business intent tags
   - allowed dimensions
   - allowed metrics

2. report registry
   - report id
   - report family
   - required filters
   - defaultable filters
   - semantic tags
   - supported dimensions
   - supported metrics
   - preferred answer patterns

3. validation rules
   - semantic tag expectations
   - zero-result suspicion rules
   - time-scope consistency rules
   - required dimension consistency rules

4. business ontology
   - domain concepts and synonyms
   - not final execution logic
   - only semantic support for model interpretation and normalization

## 7. Single-Company Invariant Policy

This ERP deployment holds only one company.

So the enterprise rule for Phase 4 is:

1. the model does not own company selection
2. the user should not need to say the company
3. the compiler injects company centrally
4. missing-company failures must disappear from the read path
5. only if a future multi-company mode is introduced should this become variable again

Implementation consequence:

- `company` must move from "user/model burden" to "compiler-injected invariant"

## 8. Clarify vs Execute vs Reject Policy

Phase 4 must choose one path explicitly.

### Execute

Use when:

1. capability can be resolved confidently
2. report selection is allowed
3. required filters are present or safely defaultable
4. no policy conflict exists

### Clarify

Use when:

1. business intent is valid but underspecified
2. missing information cannot be safely defaulted
3. two or more materially different report/capability paths remain plausible

Examples:

- user asks `show trend`
- but does not say what business object or time scope
- user asks `top 5`
- but no stable business object or metric exists yet in the first turn

### Reject

Use when:

1. request falls outside approved read path
2. requested capability/report is not governed
3. request contradicts policy
4. interpretation remains too ambiguous for safe clarification

## 9. Semantic Intent-to-Result Validation

Grounded does not automatically mean correct.

Phase 4 must add semantic result checks such as:

1. requested payable intent must not return receivable report family
2. requested revenue intent must not return zero-heavy all-period output if schema/time scope indicate mismatch
3. requested quantity intent must not return value-only output unless explicitly transformed
4. requested "all period" intent must not silently collapse into a month-specific result
5. requested ranking intent must validate that a sortable metric actually exists in the returned schema

Validation outcomes:

- `pass`
- `clarify`
- `reject_semantically_inconsistent`

Validation pipeline order:

1. deterministic schema check
2. deterministic field-presence / metric-presence check
3. deterministic semantic-tag check
4. deterministic time-scope and dimension consistency check
5. optional slower review path only if the deterministic checks are inconclusive

## 10. Runtime Boundary After Phase 4

The runtime should receive more governed input than it does now.

Instead of loosely inferring report choice, the runtime should receive a typed compiled request such as:

```json
{
  "mode": "compiled_read_query",
  "capability_id": "accounts_payable_read",
  "selected_report": "Accounts Payable Summary",
  "filters": {
    "company": "Mingalar Mobile Distribution Co., Ltd.",
    "report_date": "2026-03-22"
  },
  "requested_dimensions": [],
  "requested_metrics": ["outstanding_amount"],
  "response_policy": {
    "analysis_level": "none"
  }
}
```

This keeps the runtime useful for:

- Qwen-Agent reasoning
- tool invocation
- grounded summarization

while moving critical execution decisions into governed compiler layers.

Important topology rule:

- compiler logic should be co-located with the orchestration boundary
- do not introduce an extra network service for compiler work
- the intended shape is:
  - ERP -> compiler pipeline -> runtime execution
  - not ERP -> interpretation service -> compiler service -> runtime execution

## 11. Implementation Slices

### Slice 1: Contract and Metadata Foundation

Status:

- `completed`

Deliver:

1. `FreshQueryInterpretationContract`
2. `FreshQueryCompilerContract`
3. `CompiledQueryRequestContract`
4. `SemanticIntentValidationContract`
5. metadata extensions for:
   - closed-set intent classes
   - report family
   - semantic tags
   - defaultable filters
   - ambiguity rules

### Slice 2: Compiler Core in ERP Layer

Status:

- `completed`

Deliver:

1. capability resolution
2. deterministic report selection
3. single-company injection
4. default report-date/date-range completion
5. clarify vs execute vs reject decision
6. hardcoded-intent compiler tests before agent integration

### Slice 3: Model Proposal Integration

Status:

- `completed`

Deliver:

1. runtime-backed structured proposal generation for fresh first turns
2. typed JSON output only
3. confidence score, ambiguity flags, extracted slots
4. ranked candidate report proposals as advisory inputs only
5. no direct execution from model proposal output
6. model proposal consumed as an internal compiler sub-step, not a separate external service tier

Operational note:

- deterministic validation and compiler handoff are implemented
- direct host-to-runtime advisory verification succeeded
- backend-container-to-runtime advisory path was hardened with:
  - shared Docker network alias
  - separate fresh-query runtime timeout
  - ERP-side fresh-query timeout config
- advisory smoke pack now verifies both `execute` and `clarify` compiler outcomes

### Slice 4: Compiled Execution Path

Status:

- `completed`

Deliver:

1. typed runtime request for compiled execution
2. reduced report discovery freedom in runtime
3. governed execution trace for compiled requests

Verification note:

- compiled runtime mode now exists
- tool gateway policy constrains compiled mode to the exact governed report and filters
- compiled execution smoke passed for payable summary

### Slice 5: Semantic Result Validation

Status:

- `completed`

Deliver:

1. expected semantic tag matching
2. time-scope validation
3. dimension/metric consistency checks
4. grounded-but-wrong rejection path

Verification note:

- deterministic semantic validation now runs in ERP after compiled runtime execution
- validator decisions are explicit:
  - `pass`
  - `clarify`
  - `reject_semantically_inconsistent`
- deterministic selftests now cover:
  - governed pass case
  - governed clarify case
  - governed semantic rejection case
- real compiled payable smoke passed with:
  - compiler-selected report
  - exact governed filters
  - grounded runtime validation pass
  - semantic intent-to-result validation pass

### Slice 6: Audit and Observability

Status:

- `completed`

Deliver:

1. compiler decision audit
2. clarification audit
3. semantic validation audit
4. latency breakdown:
   - proposal generation
   - compilation
   - runtime execution
   - validation

Verification note:

- compiled first-turn path now emits a dedicated audit payload
- audit includes:
  - compiler decision
  - capability/report selection
  - grounded validation status
  - semantic validation status
  - tool count and tool names
  - per-stage latency breakdown
- deterministic Slice 6 selftest passed
- real compiled observability smoke passed for payable summary
- live-service rollout smoke passed with the compiled path enabled behind a temporary rollout flag

## 12. Phase 4 Exit Criteria

Phase 4 should close only when:

1. vague first-turn business requests compile into governed executable requests reliably
2. company is injected centrally and never causes repeated fresh-query failure
3. report selection is compiler-governed, not free-form model choice
4. missing required filters are completed or clarified before execution
5. semantically inconsistent grounded results are rejected before display
6. answer latency is measurably improved or at least more stable on first-turn read queries
7. first-turn execution no longer depends on free-form runtime report discovery

## 13. What Will Be Deferred Until After Phase 4

These remain valid, but should not outrun Phase 4:

1. generic column projection follow-ups
2. generic regroup / metric-change follow-ups
3. additional convenience follow-up expansions
4. artifact generation
5. multilingual execution behavior
6. write-path implementation

## 14. Questions To Review With Qwen Before Implementation

Please review this Phase 4 design specifically.

Questions:

1. Is this compiler boundary correct for Qwen-Agent systems?
2. Should fresh-query interpretation and follow-up interpretation share one semantic contract or stay separate?
3. Should report selection be purely compiler-selected, or compiler-selected from model-ranked candidates?
4. What is the best safe design for clarify vs execute decision?
5. What semantic result-validation checks are most important for ERP/business systems?
6. Is it better to keep compiler logic in Frappe backend, same runtime container, or another co-located boundary if we want enterprise governance without extra network hops?
7. What latency optimizations would Qwen recommend without giving report-selection freedom back to the agent?

## 15. Ready-To-Paste Prompt For Qwen

```text
Act as a senior AI/ML architect and Qwen-Agent specialist.

We are moving into Phase 4 of our enterprise ERP assistant architecture.

Our architecture rule is:
- Qwen-Agent proposes
- compiler enforces

We already completed:
- contract foundation
- read query hardening
- partial follow-up system

Our next phase is a Fresh Query Compiler.

We want first-turn business requests to compile into governed executable requests before runtime execution.

Planned Phase 4 responsibilities:
- FreshQueryInterpretationContract
- FreshQueryCompilerContract
- CompiledQueryRequestContract
- SemanticIntentValidationContract
- capability resolution
- compiler-selected report family / report id
- required filter completion
- single-company invariant injection
- default date/report-date completion
- clarify vs execute vs reject decision
- semantic intent-to-result validation

Important business constraint:
- this ERP will only ever hold one company
- company should be injected centrally, not asked from the user or delegated to the model

We want the runtime to receive a compiled request instead of loosely discovering reports.
We also want to avoid adding separate network services for interpretation and compilation if possible.

We do not want:
- phrase-specific fixes
- keyword hacks
- uncontrolled model report selection

Please review this Phase 4 design and answer:
1. Is this the right compiler boundary for Qwen-Agent?
2. Should report selection be compiler-selected or compiler-selected from model-ranked candidates?
3. Should fresh-query interpretation and follow-up interpretation share one semantic contract?
4. What is the safest clarify vs execute design?
5. What semantic intent-to-result validation checks are most important?
6. Should compiler logic live in Frappe backend, same runtime container, or another co-located boundary to reduce latency while preserving governance?
7. How would you reduce latency without giving report-selection freedom back to the model?
8. What would you change in this Phase 4 design before implementation?

Please structure your answer as:
- overall assessment
- what is correct
- what is risky
- recommended contract design
- recommended execution flow
- recommended validation design
- recommended next implementation order
```

## 16. Immediate Next Step

The next step after this planning note is:

1. keep compiled first-turn execution gated by rollout flag until we intentionally enable it
2. when ready, enable `qwen_enable_compiled_first_turn` only with governed rollout controls:
   - `qwen_compiled_first_turn_rollout_percentage`
   - `qwen_compiled_first_turn_rollout_users`
   - explicit audited fallback to legacy read-only handling for operational proposal failures during rollout
3. monitor:
   - compiler decision distribution
   - semantic validation pass/clarify/reject rates
   - proposal/runtime latency
   - compiled audit summary output from `summarize_compiled_first_turn_audits`
   - especially proposal generation latency, which is currently the dominant monitored stage
   - proposal cache hit rate on repeated governed first-turn requests
   - proposal shared-inflight hit rate under concurrent identical requests
   - rollout fallback count/rate during canary enablement
   - rollout status output from `get_compiled_first_turn_rollout_status`
   - impact of any future `SEMANTIC_FRESH_QUERY_MODEL` or `SEMANTIC_FRESH_QUERY_MAX_TOKENS` tuning on cold-path latency
4. after rollout confidence is established, resume deferred Phase 3 convenience work or begin Phase 5 artifact planning

Current production posture:

1. default to one hosted Qwen model for both proposal and runtime
2. keep separate proposal-model routing as an optional future latency lever, not the default deployment requirement
