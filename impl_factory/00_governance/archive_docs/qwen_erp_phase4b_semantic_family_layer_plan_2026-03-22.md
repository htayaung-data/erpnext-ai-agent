# Qwen ERP Phase 4B Semantic Family Layer Plan (2026-03-22)

Status: core semantic family layer implemented; governed family scope enterprise-stable; business-user closure hardening remains  
Scope: extend Phase 4 from fresh-query compilation into governed report-family abstraction, normalized business artifacts, and broad read-path expansion  
Phase goal: support broad ERP business questions through governed family routing, deterministic adapters, and composite multi-report analysis without drifting into report-by-report hacks.

## 1. Why Phase 4B Exists

Phase 4 established the correct enterprise foundation:

- `Qwen-Agent proposes`
- `compiler enforces`
- `validator confirms`

That foundation is correct, but it is not broad enough yet to support "all business-related ERP questions" in a scalable way.

The current system still reasons mainly through:

1. capability ids
2. individual report ids
3. report-specific field expectations

That is a strong improvement over free-form agent execution, but it is not yet the final enterprise abstraction.

The next scaling problem is:

- unseen ERP business questions should not require report-by-report tuning
- canonical business report families should not rely on the model inferring structure from raw ERP schema every time
- composite questions such as company health, liquidity pressure, or profitability posture cannot safely remain one-report or model-only synthesis problems

Phase 4B exists to solve that boundary.

## 2. Current Evaluation

### 2.1 What is already correct

The current architecture is already going in the right enterprise direction because it has:

1. closed-set semantic proposal contracts
2. deterministic capability and report selection
3. single-company invariant injection
4. clarify vs execute vs reject policy
5. semantic intent-to-result validation
6. audit and rollout control

This means the system is no longer behaving like a raw chatbot.

### 2.2 What is still incomplete

The current implementation is still incomplete in these important ways:

1. coverage is still narrow relative to the ERP business surface
2. major business families are not yet normalized into canonical shapes
3. common financial statements still depend too much on raw report semantics
4. composite analysis is not yet a governed first-class execution path
5. latency control still focuses on proposal/runtime, not family-level reuse and composite execution

### 2.3 Enterprise risk if we stop here

If we keep extending only by:

- more report ids
- more metadata exceptions
- more query-specific tuning

then the system will slowly become harder to maintain and harder to expand cleanly.

That would not be phrase-specific hacking, but it would still be report-specific drift.

The correct next step is to move from:

- governed reports

to:

- governed business families

### 2.4 Enterprise checkpoint after Slice 4B.6

After implementing:

1. family registry
2. financial statement adapters
3. aging adapters
4. ranking/trend adapters
5. inventory/product profitability adapters
6. compiler-approved composite read planning

the enterprise review result is:

1. the architecture is still aligned with `Qwen-Agent proposes, compiler enforces, validator confirms`
2. the project is not primarily drifting into keyword or phrase-specific fixes
3. the semantic family layer is the correct enterprise extension of Phase 4
4. the most important remaining gap is now canonical rendering discipline, not architectural direction

Checkpoint note:

- `impl_factory/00_governance/qwen_erp_phase4b_enterprise_checkpoint_note_2026-03-22.md`

### 2.5 Post-4B resilience checkpoint (2026-03-23)

After family evaluation and post-4B hardening:

1. the remaining ranking-family miss was traced to missing governed dimension/metric defaults in the proposal/fallback path
2. the correction was implemented as family-level deterministic request defaults, not query-specific answer logic
3. deterministic family-surface fallback now preserves compiler governance when runtime proposal generation is unavailable or invalid
4. the full governed family suite now passes `11/11`

Resilience note:

- `impl_factory/00_governance/qwen_erp_phase4b_post_family_proposal_resilience_note_2026-03-23.md`

### 2.6 Family latency budget checkpoint (2026-03-23)

Post-4B latency governance now exists at the family level.

Current state:

1. family latency budgets are defined in governed metadata
2. broader family evaluation sets now include latency-focused heavier families
3. the evaluation layer reports development-budget posture separately from tighter enterprise targets
4. the latest report shows the governed family layer is broadly development-acceptable, but not yet uniformly enterprise-fast

Latency note:

- `impl_factory/00_governance/qwen_erp_phase4b_family_latency_budget_note_2026-03-23.md`

### 2.7 Business-user closure checkpoint (2026-03-23)

Recent browser validation shows that the remaining gap is no longer mainly governed family execution quality.

The remaining gap is now concentrated in:

1. follow-up correction fidelity
2. ranking / metric / column fidelity
3. missing transaction-list coverage
4. broader company-health composite coverage
5. human clarification quality
6. consultant-style business insight rendering

Closure note:

- `impl_factory/00_governance/qwen_erp_phase4b_closure_hardening_plan_2026-03-23.md`

### 2.8 User-facing reset checkpoint (2026-03-23)

After Qwen consultation and browser feedback review, the next step is now explicitly defined as a user-facing reset above the governed core.

Current decision:

1. keep the governed compiler / adapter / validator core
2. move clarification wording and final narrative back toward Qwen-Agent behavior
3. treat response policy by intent as a first-class contract
4. add richer follow-up context and generic entity drilldown before adding broader new family scope

Reset note:

- `impl_factory/00_governance/qwen_erp_phase4b_user_facing_reset_plan_2026-03-23.md`

## 3. Governing Rule for Phase 4B

Phase 4B keeps the same core rule:

- `Qwen-Agent proposes business meaning`
- `compiler selects governed family and execution plan`
- `adapter normalizes ERP truth`
- `validator confirms normalized result correctness`
- `Qwen-Agent explains grounded normalized data`

Important consequence:

- adapters must not become hidden policy engines
- compiler must still approve which family and which composite plan may execute
- Qwen-Agent must not bypass family adapters by reasoning directly from raw report output when a governed family path exists

## 4. Target Architecture Extension

The target read path after Phase 4B should become:

1. user sends first-turn or follow-up business request
2. Qwen proposal layer returns:
   - intent class
   - candidate capabilities
   - candidate report families
   - requested business metrics/dimensions/time scope
   - ambiguity markers
3. compiler resolves:
   - family
   - adapter path
   - filters/invariants/defaults
   - single-family or composite execution plan
4. adapter layer executes approved ERP reports internally
5. adapter layer returns normalized family artifacts
6. validator checks:
   - family completeness
   - metric/dimension presence
   - time consistency
   - semantic consistency
   - composite completeness when relevant
7. Qwen-Agent produces grounded explanation from normalized artifacts, not raw ERP schema

## 5. New Contracts

### 5.1 `ReportFamilyContract`

Purpose:

- define the governed business family rather than only individual report ids

Minimum fields:

```json
{
  "family_id": "financial_statement",
  "family_label": "Financial Statement",
  "supported_intent_classes": ["financial_statement", "financial_summary"],
  "canonical_metrics": ["total_income", "total_expense", "net_profit"],
  "canonical_dimensions": ["account", "period"],
  "adapter_id": "financial_statement_adapter",
  "composite_allowed": true
}
```

### 5.2 `NormalizedFamilyArtifactContract`

Purpose:

- represent the adapter-normalized grounded business artifact consumed by Qwen-Agent

Minimum fields:

```json
{
  "family_id": "financial_statement",
  "artifact_type": "normalized_family_artifact",
  "source_reports": ["Profit and Loss Statement"],
  "period": {
    "from_date": "2025-04-01",
    "to_date": "2026-03-22"
  },
  "metrics": {
    "total_income": 216026500.04,
    "total_expense": 208511630.46,
    "net_profit": 7514869.58
  },
  "sections": {
    "income": [],
    "expense": [],
    "summary": []
  }
}
```

### 5.3 `CompositeReadPlanContract`

Purpose:

- represent a compiler-approved multi-family read execution plan for composite business questions

Minimum fields:

```json
{
  "plan_id": "working_capital_health",
  "request_id": "abc123",
  "decision": "execute",
  "steps": [
    {
      "family_id": "aging_receivable",
      "adapter_id": "aging_adapter",
      "metrics": ["outstanding_total", "overdue_total"]
    },
    {
      "family_id": "aging_payable",
      "adapter_id": "aging_adapter",
      "metrics": ["outstanding_total", "overdue_total"]
    }
  ],
  "compiler_reason": "company health requires governed AR and AP family artifacts"
}
```

### 5.4 `FamilyValidationContract`

Purpose:

- validate normalized family artifacts and composite outputs beyond raw report schema matching

Minimum fields:

```json
{
  "family_id": "financial_statement",
  "requested_metrics": ["total_income", "net_profit"],
  "observed_metrics": ["total_income", "total_expense", "net_profit"],
  "time_scope_match": true,
  "family_schema_match": true,
  "decision": "pass"
}
```

## 6. Initial Governed Family Set

Phase 4B should begin with the most common business families:

1. `financial_statement`
   - Profit & Loss
   - Balance Sheet
   - Cash Flow

2. `aging`
   - Accounts Receivable Aging
   - Accounts Payable Aging

3. `ranking_analytics`
   - top customers
   - top suppliers
   - top products

4. `trend_analytics`
   - monthly sales trend
   - period-over-period trend

5. `inventory_snapshot`
   - current stock/value/warehouse posture

6. `product_profitability`
   - gross profit
   - item performance

These should be governed as business families, not only as report ids.

## 7. Responsibility Split

### Qwen-Agent proposal layer

Should own:

1. messy business-language understanding
2. intent class proposal
3. family proposal
4. slot extraction
5. ambiguity detection

Should not own:

1. final report selection
2. financial calculation logic
3. canonical metric derivation
4. composite execution approval

### Compiler

Should own:

1. family resolution
2. adapter selection
3. default/invariant injection
4. composite plan approval
5. clarify vs execute vs reject decision

### Adapter layer

Should own:

1. raw ERP report execution under governed policy
2. normalization to canonical family artifact
3. transparent deterministic metric derivation
4. family-specific section extraction

Should not own:

1. policy drift
2. user-specific response decisions
3. silent business-rule invention

### Validator

Should own:

1. family schema validation
2. canonical metric presence validation
3. time/dimension consistency checks
4. composite completeness checks
5. semantic consistency checks on normalized artifacts

### Qwen-Agent runtime answer stage

Should own:

1. grounded explanation from normalized family artifacts
2. concise business interpretation when allowed by policy
3. recommendations only on explicit request and grounded support

## 8. Latency Strategy for Phase 4B

Broad coverage must not come at the cost of runaway latency.

Phase 4B should improve latency by:

1. reducing the agent decision space from raw reports to family tools
2. caching normalized family artifacts where safe
3. reusing family artifacts for follow-up questions
4. parallelizing composite family execution when policy allows
5. routing harder proposal classes to the stronger proposal model only when required
6. passing aggregated normalized artifacts to Qwen-Agent instead of raw row-heavy ERP output

Important rule:

- do not relax compiler enforcement or semantic validation just to reduce latency

## 9. Implementation Slices

### Slice 4B.1: Family Registry and Contracts

Status:

- `completed`

Deliver:

1. `ReportFamilyContract`
2. `NormalizedFamilyArtifactContract`
3. `CompositeReadPlanContract`
4. `FamilyValidationContract`
5. family registry metadata

### Slice 4B.2: Financial Statement Adapter

Status:

- `completed`

Deliver:

1. governed P&L adapter
2. governed Balance Sheet adapter
3. governed Cash Flow adapter
4. canonical financial statement schema
5. family-level validator for statement artifacts

### Slice 4B.3: Aging Adapter

Status:

- `completed`

Deliver:

1. AR aging family artifact
2. AP aging family artifact
3. normalized overdue buckets
4. canonical totals and ratios

### Slice 4B.4: Ranking and Trend Adapters

Status:

- `completed`

Deliver:

1. ranking family artifact
2. trend family artifact
3. canonical time grain handling
4. canonical dimension/metric normalization

### Slice 4B.5: Inventory and Product Profitability Adapters

Status:

- `completed`

Deliver:

1. inventory snapshot artifact
2. product profitability artifact
3. governed inventory/product summary metrics

### Slice 4B.6: Composite Read Planning

Status:

- `completed`

Deliver:

1. compiler-approved composite execution plans
2. governed multi-family execution helper
3. company health / working capital class of composite reads
4. composite audit envelope

Operational note:

- composite execution is currently serialized intentionally because Frappe runtime configuration is thread-local in the current worker model
- metadata can still declare parallel eligibility, but execution remains sequential until the runtime boundary is made thread-safe for parallel step calls

### Slice 4B.7: Family-Level Validation and Rendering

Status:

- `completed`

Deliver:

1. family schema validation
2. composite completeness validation
3. family-specific rendering policies
4. canonical response structure by family

Outcome note:

- `impl_factory/00_governance/qwen_erp_phase4b_slice7_family_validation_rendering_note_2026-03-22.md`

### Slice 4B.8: Family Tool Surface for Qwen-Agent

Status:

- `completed`

Deliver:

1. reduced high-level tool surface for Qwen-Agent
2. family tool routing instead of raw report selection where available
3. explicit policy telling Qwen-Agent to prefer family tools over raw reports

Outcome note:

- `impl_factory/00_governance/qwen_erp_phase4b_slice8_family_tool_surface_note_2026-03-22.md`

### Slice 4B.9: Evaluation and Rollout

Status:

- `completed`

Deliver:

1. family-based golden datasets
2. latency and semantic pass metrics by family
3. family rollout tracking
4. fallback monitoring by family

Outcome note:

- `impl_factory/00_governance/qwen_erp_phase4b_slice9_evaluation_rollout_note_2026-03-22.md`

## 10. Exit Criteria

Phase 4B should close only when:

1. major ERP read questions route through governed families rather than mostly report-specific paths
2. financial statements are adapter-governed, not mainly raw-report interpreted
3. composite reads are compiler-approved and auditable
4. family-level semantic validation exists and is enforced
5. unseen business phrasing can map into governed family execution without report-by-report hacks
6. latency remains controlled through reduced tool choice and normalized artifacts

Current closure status:

- `closed for the current governed family scope`
- `still open for business-user closure hardening`

Enterprise checkpoint result:

1. full governed family suite is now passing `17/17`
2. governed family enterprise-green rate is now `7/7`
3. current governed family scope is now considered enterprise-stable for:
   - financial statements
   - aging
   - ranking analytics
   - trend analytics
   - inventory snapshot
   - product profitability
   - working-capital composite health

Checkpoint note:

- `impl_factory/00_governance/qwen_erp_phase4b_enterprise_performance_stability_note_2026-03-23.md`

## 11. Immediate Next Step

The immediate next step after this note is:

1. keep Phase 4B closed for the current governed family scope at the core architecture level
2. reopen Phase 4B only for closure hardening at the business-user layer
3. implement the closure plan in this order:
   - follow-up contract hardening
   - ranking / metric / column fidelity
   - transaction-list family
   - broader company-health composite
   - human clarification layer
   - business-insight response renderer
   - closure evaluation and browser acceptance
4. keep expanding by contracts and families, not by isolated query patches
5. preserve deterministic execution, family normalization, and validator-first rendering as the default enterprise read boundary

Closure plan note:

- `impl_factory/00_governance/qwen_erp_phase4b_closure_hardening_plan_2026-03-23.md`
