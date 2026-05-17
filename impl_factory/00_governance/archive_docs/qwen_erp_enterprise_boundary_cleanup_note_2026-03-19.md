# Qwen ERP Enterprise Boundary Cleanup Note (2026-03-19)

Status: completed with known gaps  
Scope: enterprise cleanup pass before continuing Phase 3 follow-up expansion  
Purpose: restore clean architectural boundaries after follow-up handling started drifting into heuristic and capability-specific logic inside generic layers.

## Why This Cleanup Was Required

During Phase 3 implementation, several useful fixes had started to cross architectural boundaries:

1. follow-up detection was relying on direct alias and prefix heuristics inside generic contract flow
2. report-family shaping logic for payable ageing was living inside the generic service layer
3. grounded table extraction logic had started to encode report-specific assumptions inside the contract layer
4. ERP-side runtime request fields had been added without being consumed by the runtime, creating contract drift

This cleanup pass was required to keep the project aligned with enterprise architecture standards rather than letting short-term fixes accumulate inside shared orchestration code.

## What Was Changed

### 1. Follow-up interpretation isolated into its own layer

Added:

- `/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/followup_interpreter.py`

Responsibility:

1. normalize follow-up text
2. interpret requested follow-up modes
3. detect self-contained business requests
4. keep heuristic interpretation isolated from contracts and execution logic

Result:

The contract layer now consumes a structured `FollowUpIntent` instead of embedding direct matching behavior.

### 2. Capability-specific local transforms moved into adapters

Added:

- `/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/capability_adapters.py`

Responsibility:

1. extract grounded tables from approved report outputs
2. render metadata-driven local follow-up views
3. support capability-specific local transforms such as payable ageing bucket views

Result:

The generic service layer no longer owns payable ageing rendering logic.

### 3. Shared metadata strengthened to support adapters

Updated:

- `/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/report_registry.json`

Added metadata for approved financial report families:

1. supplemental fields
2. local follow-up adapter definitions
3. ageing bucket labels
4. total outstanding and total due field mappings

Result:

Capability-specific shaping now depends on governed metadata instead of generic Python branching.

### 4. Contracts refactored back toward generic responsibility

Updated:

- `/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/contracts.py`

Changes:

1. grounded table extraction now delegates to capability adapters
2. follow-up resolution now delegates to the follow-up interpreter
3. ageing bucket support checks now delegate to adapters
4. generic contract code no longer carries payable-specific report shape logic

### 5. Runtime contract drift removed

Updated:

- `/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/runtime_client.py`
- `/home/deploy/erp-projects/erpai_project1/experimental/qwen_agent_runtime/app/schemas.py`

Removed unused request fields that were not being consumed by the runtime:

1. `requested_modes`
2. `target_capability_id`
3. `target_report`
4. `source_report`
5. `display_preferences`
6. `grounded_filters`

Result:

The ERP-to-runtime contract is again aligned with actual runtime behavior.

## Verification Performed

Verified end to end in a fresh session:

1. `How much payable amount do we have as of today`
   - resolved as `new_query`
   - execution path `erp_requery`
   - grounded approved source: `Accounts Payable Summary`

2. `Show by Period of due`
   - resolved as `local_grounded_transform`
   - execution path `local_transform`
   - rendered from stored grounded context through capability adapters

3. `Show in Million`
   - resolved as `local_grounded_transform`
   - execution path `local_transform`
   - applied on top of the grounded due-period view without ERP requery

The verification confirmed that the cleanup preserved behavior while improving boundary discipline.

## Enterprise Assessment After Cleanup

This cleanup improved the architecture materially:

1. generic layers are cleaner
2. capability-specific behavior is more explicitly owned
3. metadata is more central
4. runtime contract drift was removed

However, one important gap remains:

The follow-up interpreter is now isolated, but it is still heuristic. That is acceptable as an isolated compatibility layer for now, but it is not the final enterprise-standard answer.

The long-term enterprise target remains:

1. typed follow-up interpretation
2. ontology-backed evidence
3. capability-aware resolution
4. deterministic execution path selection

## What Remains Intentionally Deferred

This cleanup did not yet implement:

1. full typed follow-up parser
2. column projection adapter layer
3. local sort and limit transforms
4. sibling-switch resolution from capability metadata
5. multilingual follow-up interpretation

Those remain the next proper slices of Phase 3.

## Exit Decision

This boundary cleanup pass is:

`completed with known gaps`

It is sufficient to continue Phase 3 from a cleaner enterprise base, but it does not close the broader follow-up-system phase.
