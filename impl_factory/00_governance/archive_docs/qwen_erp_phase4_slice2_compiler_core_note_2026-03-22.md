# Qwen ERP Phase 4 Slice 2 Compiler Core Note (2026-03-22)

Status: completed  
Scope: Phase 4 Slice 2 from the Fresh Query Compiler plan  
Slice goal: establish the deterministic compiler core in the ERP layer before model proposal integration.

## Objective

This slice introduces the first real compiler logic for fresh first-turn queries.

The goal is to make these decisions deterministic and metadata-governed:

1. capability resolution
2. report selection
3. single-company invariant injection
4. default filter completion
5. clarify vs execute vs reject decision

This slice intentionally precedes model proposal integration.

## What Was Implemented

### 1. Compiler core module

Added [compiler.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/compiler.py).

It implements:

1. deterministic capability resolution from governed metadata
2. deterministic report selection from governed metadata
3. defaultable filter application
4. single-company invariant lookup from ERP
5. ambiguity-rule evaluation
6. compiler decision output through:
   - `FreshQueryCompilerContract`
   - `CompiledQueryRequestContract`

### 2. Metadata accessors needed by the compiler

Updated [metadata.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/metadata.py) with:

1. `list_capability_specs`
2. `capability_report_names`
3. `capability_default_report_name`

These accessors keep the compiler metadata-driven instead of embedding registry traversal in execution code.

### 3. Hardcoded-intent compiler selftests

Added `run_phase4_compiler_selftests()` in [compiler.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/compiler.py).

This verifies two governed cases before model integration:

1. payable summary intent
   - compiles to `execute`
   - injects company and report date
   - produces a `CompiledQueryRequestContract`
2. trend analysis without time scope
   - compiles to `clarify`
   - does not produce a compiled execution request

### 4. Transition-safe runtime invariant activation

Enabled `ERP_DEFAULT_COMPANY` in [experimental/qwen_agent_runtime/.env](/home/deploy/erp-projects/erpai_project1/experimental/qwen_agent_runtime/.env) and documented it in [experimental/qwen_agent_runtime/.env.example](/home/deploy/erp-projects/erpai_project1/experimental/qwen_agent_runtime/.env.example).

This does not replace the future compiler path.

It is a safe bridge improvement because:

1. the runtime already had generic company injection support
2. this ERP deployment is single-company by policy
3. it removes a known class of repeated fresh-query failures during the transition to compiled execution

## What Was Intentionally Not Done Yet

This slice does **not** yet implement:

1. model proposal generation for fresh first turns
2. compiled runtime request execution from the live ERP path
3. semantic intent-to-result validation enforcement
4. compiler-driven live user query routing

Those belong to later Phase 4 slices.

## Verification Performed

Verified:

1. Python compile passed for the ERP-side Qwen chat module after compiler addition
2. `run_phase4_compiler_selftests()` passed through Bench
3. runtime was rebuilt successfully after enabling `ERP_DEFAULT_COMPANY`
4. runtime health remained healthy
5. direct runtime smoke for:
   - `How much payable amount do we have as of now`
   returned:
   - grounded answer
   - approved report `Accounts Payable Summary`
   - validation `pass`

## Important Architectural Note

This slice creates compiler logic but does not yet make the live chat path compiler-driven.

That is intentional.

The enterprise order remains:

1. compiler core first
2. model proposal integration second
3. compiled execution path after that

This avoids mixing fresh-query language understanding and deterministic compiler logic into one uncontrolled implementation step.

## Exit Decision

Slice 2 is:

- `completed`

## Next Slice

The next Slice 3 work should integrate model proposals into the compiler path:

1. structured fresh-query proposal generation
2. closed-set intent class output
3. advisory candidate reports
4. proposal consumed as a compiler sub-step, not a standalone service tier
