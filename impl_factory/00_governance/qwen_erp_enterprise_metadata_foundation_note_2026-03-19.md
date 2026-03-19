# Qwen ERP Enterprise Metadata Foundation Note (2026-03-19)

Status: completed with known gaps  
Scope: enterprise metadata normalization before Phase 3  
Goal: replace runtime-local governance data with a shared metadata foundation that both ERP-side logic and the Qwen runtime consume as one governed source of truth.

## Why This Was Needed

Phase 2 introduced governed report approval and validation, but the first implementation still kept important governance data too close to runtime code:

1. approved reports lived in a runtime-local registry
2. follow-up semantics still depended partly on local heuristics
3. validation rules were not yet separated as first-class governed metadata

That direction was better than scattered conditionals, but it was not yet strong enough for an enterprise architecture.

The required correction was:

1. separate metadata from runtime code
2. let ERP-side and runtime-side layers read the same governed data
3. make capability, ontology, report, and validation concerns explicit and independently maintainable

## What Was Implemented

### 1. Shared enterprise metadata directory

Created:

- `/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/`

Files added:

1. `capability_registry.json`
2. `report_registry.json`
3. `business_ontology.json`
4. `validation_rules.json`
5. `README.md`

This directory is now the governed metadata source of truth for the Qwen ERP path.

### 2. Runtime now reads shared metadata

Updated:

- `/home/deploy/erp-projects/erpai_project1/experimental/qwen_agent_runtime/app/report_registry.py`
- `/home/deploy/erp-projects/erpai_project1/experimental/qwen_agent_runtime/app/validation.py`
- `/home/deploy/erp-projects/erpai_project1/experimental/qwen_agent_runtime/docker-compose.yml`

Behavior changes:

1. runtime report policy is no longer backed by a local JSON file inside the runtime app
2. runtime capability, report, and validation policy now come from the shared metadata directory
3. the obsolete runtime-local `report_registry.json` was removed

### 3. ERP-side follow-up logic now reads shared ontology metadata

Added:

- `/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/metadata.py`

Updated:

- `/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/contracts.py`
- `/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py`

Behavior changes:

1. follow-up aliases are now read from `business_ontology.json`
2. business-term detection for self-contained requests is now metadata-backed
3. presentation-transform detection uses governed ontology aliases instead of isolated literals

### 4. ERP containers now mount the same shared metadata

Updated:

- `/home/deploy/erp-projects/erpai_project1/compose.yaml`

Added to ERP Python services:

1. read-only bind mount for `impl_factory/03_config/qwen_enterprise_metadata`
2. `QWEN_ENTERPRISE_METADATA_DIR=/home/frappe/frappe-bench/qwen_enterprise_metadata`

This ensures the ERP-side contract layer and the runtime use the same metadata source rather than drifting into separate copies.

## What This Change Improves

This move changes the governance shape in an important way:

1. report approval is now metadata-governed, not runtime-local
2. capability definitions are separated from report definitions
3. business terminology and follow-up aliases have a dedicated ontology file
4. validation profiles are governed as metadata, not hidden inside one validator
5. ERP-side and runtime-side interpretation now share the same contract vocabulary

This is materially closer to enterprise architecture than growing more code branches inside the agent runtime.

## Verification Performed

Technical verification completed after the refactor:

1. shared metadata was mounted successfully inside the ERP backend container
2. ERP-side metadata loader resolved the shared directory correctly
3. runtime still loaded:
   - `7` approved reports
   - `4` capabilities
   - `2` validation profiles
4. governed read regressions still passed:
   - `show sales last month`
   - `How much we need to pay as Payable as of now?`
   - `stock by warehouse`
5. validated reports remained explicit and correct:
   - `Sales Analytics`
   - `Accounts Payable Summary`
   - `Warehouse Wise Stock Balance`
6. hidden per-turn records still persisted:
   - `qwen_interaction_contract`
   - `qwen_followup_resolution`
   - `qwen_execution_path`
   - `qwen_grounded_turn_context`
   - `qwen_audit_envelope`

## What This Does Not Yet Solve

This metadata foundation is enterprise-shaped, but not yet enterprise-complete.

Still intentionally deferred:

1. richer capability families beyond the current approved read set
2. multilingual ontology and glossary coverage
3. artifact metadata for tables, charts, and dashboards
4. write-action policy metadata
5. confidence/retry policy metadata
6. separate read/write service-user security model

## Relationship To Phase 2

This note does not replace Phase 2.

It hardens Phase 2 by moving its governance assets into a cleaner enterprise structure.

Historical view:

1. Phase 2 proved report governance and validation behavior
2. this metadata foundation normalized where that governance should live

## Exit Decision

This metadata normalization is considered:

`completed`

Reason:

1. one shared governed metadata source now exists
2. both ERP-side and runtime-side layers consume it
3. governed read behavior remains stable after the refactor

## Next Step

Proceed to Phase 3 only on top of this shared metadata foundation.

That means:

1. follow-up classes should extend capability/ontology metadata, not branchy code
2. local transforms, projection, refinement, and sibling-switch logic should read governed context and metadata first
