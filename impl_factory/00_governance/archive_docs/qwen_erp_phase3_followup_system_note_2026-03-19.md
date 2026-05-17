# Qwen ERP Phase 3 Follow-Up System Note (2026-03-19)

Status: in progress  
Scope: enterprise Phase 3 from the Qwen ERP blueprint  
Phase goal: move follow-up handling from ad hoc model behavior toward typed, grounded, metadata-driven resolution.

## Consultation Correction

After Qwen-Agent architecture consultation, the steering correction for Phase 3 is:

1. Phase 3 remains necessary, but it should stay bounded to governed follow-up behavior
2. Phase 3 should not keep expanding while first-turn fresh-query compilation remains under-governed
3. the permanent architectural direction is:
   - `Qwen-Agent` proposes semantic intent
   - deterministic compiler and policy layers enforce execution
4. separate semantic interpretation round-trips are acceptable as a bounded reliability measure, but should not become the long-term center of the architecture if the compiler can safely absorb that responsibility later

## Current Slices Implemented

The implemented Phase 3 slices are:

1. `metadata-driven local grounded follow-up transforms`
2. `schema-aware local dimension breakdown follow-ups`
3. `metadata-governed local sort and limit follow-ups`
4. `semantic follow-up interpretation with runtime-backed typed contracts`
5. `semantic confidence policy and degraded-mode control`
6. `response policy enforcement for factual vs analytical answers`

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

### 5. Metadata-governed local sort and limit follow-ups

Updated:

- `/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/report_registry.json`
- `/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/followup_interpreter.py`
- `/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/contracts.py`
- `/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/capability_adapters.py`
- `/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py`

Behavior added:

1. interpret follow-ups like `Top 3 supplier`, `top 5`, `highest`, and `lowest`
2. carry structured sort intent through the follow-up contract using `target_limit` and `sort_direction`
3. rank grounded rows locally without ERP requery
4. prefer governed adapter metadata for dimension and metric selection on financial report families
5. allow presentation transforms like `show as million` to apply after the local ranking step
6. expand or shrink ranked follow-ups from the full grounded dataset, not from the previously displayed subset

### 6. Semantic follow-up interpretation with typed contracts

Updated:

- `/home/deploy/erp-projects/erpai_project1/experimental/qwen_agent_runtime/app/semantic_followup_engine.py`
- `/home/deploy/erp-projects/erpai_project1/experimental/qwen_agent_runtime/app/schemas.py`
- `/home/deploy/erp-projects/erpai_project1/experimental/qwen_agent_runtime/app/main.py`
- `/home/deploy/erp-projects/erpai_project1/experimental/qwen_agent_runtime/app/service.py`
- `/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/semantic_interpreter.py`
- `/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/runtime_client.py`
- `/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/contracts.py`
- `/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py`
- `/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/metadata.py`
- `/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/capability_registry.json`

Behavior added:

1. the ERP layer no longer relies on phrase aliases as the primary follow-up interpreter
2. when a grounded turn exists, ERP sends a typed interpretation request to the Qwen runtime
3. the Qwen runtime returns structured JSON for:
   - `requested_modes`
   - `target_dimension`
   - `target_limit`
   - `sort_direction`
   - `target_capability_id`
   - `self_contained`
4. ERP validates that interpretation against governed metadata:
   - approved follow-up modes for the source report
   - allowed dimensions
   - allowed sibling capabilities
5. only after validation does ERP choose:
   - `local_transform`
   - `capability_requery`
   - `grounded_follow_up`
   - `new_query`
6. the old heuristic matcher remains only as a degraded fallback when semantic interpretation is unavailable

### 7. Semantic confidence policy, degraded-mode audit, and interpreter hardening

Updated:

- `/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/semantic_interpreter.py`
- `/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/followup_interpreter.py`
- `/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/contracts.py`
- `/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py`
- `/home/deploy/erp-projects/erpai_project1/experimental/qwen_agent_runtime/app/semantic_followup_engine.py`
- `/home/deploy/erp-projects/erpai_project1/experimental/qwen_agent_runtime/app/settings.py`

Behavior added:

1. semantic follow-up interpretation now has a governed confidence threshold
2. low-confidence or invalid semantic interpretations are explicitly recorded as degraded mode
3. heuristic fallback is no longer silent
4. compatibility fallback is limited to safe local presentation/order transforms
5. runtime follow-up interpretation now includes:
   - retry/backoff
   - JSON repair fallback
   - telemetry for attempts, latency, and repair usage

This makes degraded behavior visible and auditable instead of silently blending semantic and heuristic paths.

### 8. Response policy moved from governance-only into runtime-enforced contract flow

Updated:

- `/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/contracts.py`
- `/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/runtime_client.py`
- `/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py`
- `/home/deploy/erp-projects/erpai_project1/experimental/qwen_agent_runtime/app/schemas.py`
- `/home/deploy/erp-projects/erpai_project1/experimental/qwen_agent_runtime/app/qwen_agent_engine.py`

Behavior added:

1. each turn now records a `qwen_response_policy_contract`
2. the runtime receives explicit response-policy context with the request
3. factual default turns are instructed to:
   - present grounded facts first
   - include table/breakdown when relevant
   - avoid automatic recommendations
4. explicitly analytical turns are instructed to allow deeper interpretation only when grounded or explicitly derived

## What This Phase Does Not Own

Phase 3 does not own:

1. final report selection for fresh first-turn business requests
2. single-company invariant injection
3. required filter completion for fresh queries
4. semantic intent-to-result validation for first-turn execution

Those responsibilities now belong to the Phase 4 compiler path.

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

4. separate fresh session:
   - `How much payable amount do we have as of today`
   - `Top 3 supplier`
   - `show as million`
   - resolved as:
     - first turn: `new_query` -> `erp_requery`
     - second turn: `local_grounded_transform` with `requested_modes = [sort_or_limit]`, `target_limit = 3`, `sort_direction = desc`
     - third turn: `local_grounded_transform` with `requested_modes = [presentation_transform]`
   - local ranking used governed financial metadata and rendered:
     - `Supplier`
     - `Outstanding (MMK)`
   - no ERP requery was required for the second or third turn

5. separate fresh session:
   - `How about Receivable`
   - `Top 5 customers show as table`
   - `give me top 7 customers`
   - resolved as:
     - first turn: `new_query` -> `erp_requery`
     - second turn: `local_grounded_transform` with `requested_modes = [table_presentation, sort_or_limit]`, `target_limit = 5`, `sort_direction = desc`
     - third turn: `local_grounded_transform` with `requested_modes = [sort_or_limit]`, `target_limit = 7`, `sort_direction = desc`
   - third turn correctly expanded from the full grounded receivable dataset and rendered customers 6 and 7:
     - `Latha Mobile Wholesale`
     - `Shwe Li Road Mobile Wholesale`
   - no ERP requery was required for the second or third turn

6. separate fresh session after semantic interpreter replacement:
   - `How much payable amount do we have as of now`
   - `Show me by suppliers`
   - `How about receivable`
   - resolved as:
     - second turn: `local_grounded_transform` with `requested_modes = [dimension_breakdown]`, `target_dimension = Supplier`
     - third turn: `capability_requery` with `requested_modes = [sibling_switch]`, `target_capability_id = accounts_receivable_read`, `target_report = Accounts Receivable Summary`
   - this fixed wording variants that previously failed because they did not match narrow phrase aliases

7. separate fresh session:
   - `How much payable amount do we have as of now`
   - `Show receivable amount by customers`
   - resolved as:
     - second turn: `capability_requery` into `Accounts Receivable Summary`
   - wording no longer depends on a narrow `how about receivable` phrase family

## Important Finding

One crash observed during this slice was not a follow-up logic issue.

Cause:

1. two chat sends were accidentally fired in parallel against the same session
2. Frappe correctly raised `TimestampMismatchError`

This is a session concurrency issue, not a grounding or follow-up resolution failure.

## Product Behavior To Preserve

The current answer style exposed an important product strength that should now be treated as governed behavior:

1. grounded facts first
2. supporting table or numeric breakdown next
3. concise business interpretation after the facts
4. recommendations only when clearly supported by grounded or explicitly derived data
5. no automatic recommendations in default factual answers
6. fuller insight and recommendations only when the user explicitly asks for analysis, interpretation, comparison, or recommendation

This pattern should be preserved as the system expands because it matches the needs of business users, managers, and executives better than either raw report dumps or overly chatty narrative answers.

## What Is Still Not Done In Phase 3

Phase 3 is not complete yet.

Still pending:

1. column projection from grounded tables
2. filter refinement and regrouping from grounded context
3. stronger follow-up audit detail for applied vs requested transforms
4. clarify policy when semantic interpretation is low-confidence and no safe compatibility fallback exists
5. reducing runtime latency variance on semantic follow-up + ERP requery chains

## Steering Decision After Consultation

Phase 3 should now be treated as:

- a governed follow-up reliability layer
- a deterministic local-transform layer
- not the primary place to solve first-turn reliability

So the next primary engineering push should move to:

- `FreshQueryCompilerContract`
- invariant injection
- compiler-selected report execution
- semantic intent-to-result validation

## Exit State

Phase 3 remains:

`in progress`

This note records the first stable slice, not full phase closure.
