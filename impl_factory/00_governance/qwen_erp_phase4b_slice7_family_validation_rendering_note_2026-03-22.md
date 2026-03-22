# Qwen ERP Phase 4B Slice 7 Family Validation and Rendering Note (2026-03-22)

Status: completed  
Scope: tighten family/composite validation and make compiled first-turn answers render from governed normalized artifacts instead of relying on runtime prose  
Result: canonical family/composite rendering is now part of the governed read path.

## 1. Why Slice 4B.7 Was Needed

After Slice 4B.6, the architecture had the correct enterprise core:

1. governed family adapters
2. normalized family artifacts
3. compiler-approved composite reads
4. family/composite validation payloads

But one important boundary was still weak:

- final user-visible answer text could still depend too much on runtime natural-language output instead of deterministic normalized business artifacts

That was not a correctness disaster, but it was not the right enterprise finish for the family layer.

Slice 4B.7 closes that gap.

## 2. What Was Implemented

### 2.1 Render contracts

New governed rendering contracts were added so family/composite rendering is explicit and auditable:

1. `RenderedFamilyResponseContract`
2. `CompositeReadValidationContract`

These now sit beside:

1. `NormalizedFamilyArtifactContract`
2. `FamilyValidationContract`
3. `CompositeReadPlanContract`

### 2.2 Renderer metadata

Family metadata now includes governed renderer ids in:

- `report_family_registry.json`

Examples:

1. `financial_statement_renderer`
2. `aging_renderer`
3. `ranking_renderer`
4. `trend_renderer`
5. `inventory_snapshot_renderer`
6. `product_profitability_renderer`

Composite planning already had:

1. `working_capital_health_renderer`

### 2.3 Deterministic family renderers

A new rendering layer now builds canonical answer structures for:

1. financial statements
2. aging
3. ranking analytics
4. trend analytics
5. inventory snapshot
6. product profitability
7. composite working-capital health

These renderers produce:

1. canonical title
2. summary table
3. family-specific data table or bullet section
4. deterministic markdown answer text

### 2.4 Validation tightening

Family validators were tightened so normalized artifacts must now preserve:

1. governed source reports
2. required summary sections
3. family-specific structural completeness

Composite validation is now governed through a formal composite validation contract instead of only an ad hoc payload shape.

### 2.5 Service-path enforcement

Compiled first-turn display now prefers:

1. rendered family/composite response contract

before:

1. runtime natural-language answer text

This means the live compiled path now behaves as:

- compiler -> runtime/tool result -> normalized artifact -> validator -> canonical renderer -> user-visible answer

That is the right enterprise boundary.

## 3. Files Updated

Primary implementation files:

1. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/contracts.py`
2. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/family_rendering.py`
3. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/family_validator.py`
4. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/fresh_query_interpreter.py`
5. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/composite_reads.py`
6. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py`
7. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/semantic_validator.py`
8. `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/metadata.py`
9. `experimental/qwen_agent_runtime/app/report_registry.py`
10. `impl_factory/03_config/qwen_enterprise_metadata/report_family_registry.json`

## 4. Verification

Verification passed for:

1. Python compile
2. metadata JSON validation
3. existing financial family smoke
4. composite read smoke
5. new full rendering smoke across:
   - financial statement
   - aging
   - ranking analytics
   - trend analytics
   - product profitability
   - composite working-capital health
6. live service-path regression confirming rendered answer text is what the user sees

Important real bug found and fixed during verification:

- `trend_analytics` was being rejected by family/semantic validation because the validator still treated extra requested metrics as mandatory even when the governed trend artifact is single-metric
- this was corrected so validation now follows the governed family design instead of over-rejecting valid trend artifacts

## 5. Enterprise Outcome

After Slice 4B.7:

1. normalized artifacts are not just audit payloads
2. canonical rendering is now a first-class governed stage
3. family/composite display is less dependent on runtime prose drift
4. the read path is more auditable and more stable across business families

This is a meaningful enterprise hardening step.

## 6. Remaining Known Limits

The most important remaining limits are:

1. composite execution is still serialized intentionally for correctness
2. family tool-surface reduction for Qwen-Agent is not implemented yet
3. family-based evaluation and rollout governance still need their own slice
4. broad ERP coverage still continues family by family

## 7. Next Step

The next implementation step after Slice 4B.7 is:

1. Slice 4B.8: family tool surface for Qwen-Agent

That slice should reduce direct raw-report choice where a governed family tool exists, so the runtime decision surface becomes smaller and more stable.
