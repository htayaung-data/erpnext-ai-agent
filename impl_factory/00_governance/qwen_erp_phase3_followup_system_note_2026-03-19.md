# Qwen ERP Phase 3 Follow-Up System Note (2026-03-19)

Status: in progress  
Scope: enterprise Phase 3 from the Qwen ERP blueprint  
Phase goal: move follow-up handling from ad hoc model behavior toward typed, grounded, metadata-driven resolution.

## Current Slices Implemented

The implemented Phase 3 slices are:

1. `metadata-driven local grounded follow-up transforms`
2. `schema-aware local dimension breakdown follow-ups`

This slice addresses follow-ups that should not require a fresh ERP requery when the latest grounded turn already contains sufficient structured context.

## What Was Added

### 1. Metadata-driven follow-up mode detection

Updated:

- `/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/business_ontology.json`
- `/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/metadata.py`
- `/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/contracts.py`

Added ontology support for:

1. `presentation_transform`
2. `table_presentation`
3. `dimension_breakdown`

The resolver now detects requested follow-up modes from shared ontology metadata rather than hand-coded string branches.

### 2. New typed follow-up modes

Updated:

- `/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/contracts.py`

Added:

- `FollowUpResolution.requested_modes`
- `FollowUpResolution.mode = local_grounded_transform`
- `FollowUpResolution.target_dimension`

This mode is used when:

1. a prior grounded turn exists
2. the new request is a presentation-level follow-up
3. the requested transformation can be resolved from stored grounded context

### 3. Local grounded execution for compound follow-ups

Updated:

- `/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py`

Behavior added:

1. local table materialization from `GroundedTurnContext.returned_schema` + `table_rows`
2. local million-unit transformation layered on top of grounded results
3. compound follow-up handling such as:
   - `Show in Million, and provide Payable amount per supplier as Table`

This keeps the answer grounded without asking the model/runtime to rediscover the same report.

### 4. Schema-aware dimension breakdowns from grounded context

Updated:

- `/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/report_registry.json`
- `/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/followup_interpreter.py`
- `/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/capability_adapters.py`
- `/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/contracts.py`
- `/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py`

Behavior added:

1. interpret elliptical follow-ups like `Show by supplier` against grounded report metadata
2. map the requested business dimension to a governed local adapter
3. render supplier/customer breakdown tables from stored grounded rows without ERP requery
4. allow presentation transforms like `show as million` to apply on top of those locally rendered breakdowns

## Verification Performed

Verified in fresh ordered sessions:

1. first turn:
   - `How much we need to pay as Payable as of now?`
   - grounded successfully from approved report `Accounts Payable Summary`
2. second turn:
   - `Show in Million, and provide Payable amount per supplier as Table`
   - resolved as:
     - `followup_mode = local_grounded_transform`
     - `requested_modes = [presentation_transform, table_presentation]`
     - `execution_path = local_transform`
   - no new ERP requery was required

3. separate fresh session:
   - `How much payable amount do we have as of today`
   - `Show by supplier`
   - `show as million`
   - resolved as:
     - first turn: `new_query` -> `erp_requery`
     - second turn: `local_grounded_transform` with `requested_modes = [dimension_breakdown]` and `target_dimension = Supplier`
     - third turn: `local_grounded_transform` with `requested_modes = [presentation_transform]`
   - no ERP requery was required for the second or third turn

## Important Finding

One crash observed during this slice was not a follow-up logic issue.

Cause:

1. two chat sends were accidentally fired in parallel against the same session
2. Frappe correctly raised `TimestampMismatchError`

This is a session concurrency issue, not a grounding or follow-up resolution failure.

## What Is Still Not Done In Phase 3

Phase 3 is not complete yet.

Still pending:

1. column projection from grounded tables
2. local sort/limit transforms
3. filter refinement and regrouping from grounded context
4. sibling-switch handling from capability metadata
5. stronger follow-up audit detail for applied vs requested transforms
6. replacing heuristic follow-up interpretation with a fully typed parser

## Exit State

Phase 3 remains:

`in progress`

This note records the first stable slice, not full phase closure.
