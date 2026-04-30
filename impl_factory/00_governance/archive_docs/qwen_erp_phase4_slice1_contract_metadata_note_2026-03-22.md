# Qwen ERP Phase 4 Slice 1 Contract and Metadata Foundation Note (2026-03-22)

Status: completed  
Scope: Phase 4 Slice 1 from the Fresh Query Compiler plan  
Slice goal: establish the shared contracts and metadata required for compiler-governed first-turn query execution.

## Objective

This slice exists to make Phase 4 possible without mixing compiler logic into ad hoc code paths.

It establishes:

1. typed compiler contracts
2. shared metadata for closed-set intent classes
3. report semantic tags and defaultable filters
4. validation metadata for future semantic intent-to-result checks

No fresh-query compiler behavior is implemented in this slice yet.

## What Was Implemented

### 1. New Phase 4 contracts in ERP-side code

Added to [contracts.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/contracts.py):

1. `FreshQueryInterpretationContract`
2. `FreshQueryCompilerContract`
3. `CompiledQueryRequestContract`
4. `SemanticIntentValidationContract`

Added builder functions for all four contracts so later slices can use typed payload generation instead of inline dictionaries.

### 2. Capability registry extensions

Updated [capability_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/capability_registry.json) with:

1. top-level closed-set `intent_classes`
2. per-capability `intent_classes`
3. per-capability `semantic_tags`

This creates the compiler-side vocabulary for:

- financial summary
- ranked entities
- trend analysis
- inventory summary
- aging analysis

### 3. Report registry extensions

Updated [report_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/report_registry.json) with:

1. `defaultable_filters`
2. `supported_intent_classes`
3. `semantic_tags`

This is the first metadata layer that makes it possible to:

- inject the single-company invariant from metadata
- distinguish report families semantically
- map compiler intent classes to allowed reports

### 4. Validation metadata extensions

Updated [validation_rules.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/validation_rules.json) with:

1. semantic validation requirements on the grounded-read profile
2. deterministic semantic validation order
3. ambiguity rules for trend and ranking intents

This prepares the later semantic intent-to-result validation layer without implementing runtime behavior yet.

### 5. Metadata helper extensions

Updated [metadata.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/metadata.py) and [report_registry.py](/home/deploy/erp-projects/erpai_project1/experimental/qwen_agent_runtime/app/report_registry.py) with helpers for:

1. loading validation rules
2. listing and resolving intent classes
3. reading report semantic tags
4. reading report defaultable filters
5. reading supported intent classes
6. reading semantic validation policy and ambiguity rules

## What Was Intentionally Not Done Yet

This slice does **not** yet implement:

1. fresh-query interpretation behavior
2. compiler selection logic
3. company injection behavior
4. compiled runtime request execution
5. semantic validation enforcement

Those belong to later Phase 4 slices.

## Verification Performed

Verified:

1. JSON validation passed for:
   - [capability_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/capability_registry.json)
   - [report_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/report_registry.json)
   - [validation_rules.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/validation_rules.json)
2. Python compile passed for:
   - [contracts.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/contracts.py)
   - [metadata.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/metadata.py)
   - [report_registry.py](/home/deploy/erp-projects/erpai_project1/experimental/qwen_agent_runtime/app/report_registry.py)

## Exit Decision

Slice 1 is:

- `completed`

## Next Slice

The next Slice 2 work should implement the compiler core in the ERP layer:

1. capability resolution
2. deterministic report selection
3. single-company invariant injection
4. default completion
5. clarify vs execute vs reject decision
