# Qwen ERP Phase 4 Slice 4 Compiled Execution Note (2026-03-22)

Status: implemented and smoke-verified  
Scope: Phase 4 Slice 4 compiled execution path for governed first-turn read queries

## Purpose

This slice makes the runtime capable of accepting a governed compiled request instead of rediscovering reports freely.

The architecture rule remains:

- `Qwen-Agent proposes`
- `compiler enforces`

In this slice:

- the compiler still decides the report and filters
- the runtime receives a typed compiled request
- the runtime is constrained to execute only that governed request

## What Was Implemented

### Runtime Request Contract Plumbing

Extended runtime chat requests to carry compiled request data:

- `experimental/qwen_agent_runtime/app/schemas.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/runtime_client.py`

Added:

1. `compiled_query` payload on `ChatRequest`
2. `compiled_read_query` runtime mode support

### Runtime Execution Constraint

Implemented compiled-mode execution control in:

- `experimental/qwen_agent_runtime/app/qwen_agent_engine.py`
- `experimental/qwen_agent_runtime/app/tool_gateway_policy.py`
- `experimental/qwen_agent_runtime/app/service.py`

Compiled-mode rules now include:

1. runtime mode may be `compiled_read_query`
2. compiled mode system contract tells Qwen-Agent:
   - use only `erp_fac-generate_report`
   - do not call `report_list`
   - do not call `report_requirements`
   - use the exact governed `report_name`
   - use the exact governed `filters`
3. tool gateway policy enforces:
   - only `erp_fac-generate_report` is allowed in compiled mode
   - report name must exactly match the compiled request
   - filters must exactly match the compiled request
   - normal report approval and filter validation still apply

### ERP-Side Smoke Helper

Added compiled execution smoke helper in:

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/fresh_query_interpreter.py`

Helper:

- `run_phase4_compiled_execution_smoke`

It performs:

1. fresh-query interpretation
2. compiler execution contract creation
3. runtime `compiled_read_query` execution

## Verification

Passed:

1. `python3 -m compileall ...`
2. runtime rebuild and health check
3. `bench execute ai_assistant_ui.qwen_chat.fresh_query_interpreter.run_phase4_compiled_execution_smoke`

Smoke result:

1. fresh-query interpretation accepted payable summary intent
2. compiler selected:
   - capability `accounts_payable_read`
   - report `Accounts Payable Summary`
   - filters:
     - `company = Mingalar Mobile Distribution Co., Ltd.`
     - `report_date = 2026-03-22`
3. runtime executed only one tool call:
   - `erp_fac-generate_report`
4. validation passed
5. grounded final answer returned successfully

This confirms that Slice 4 now supports:

- typed compiled request handoff
- reduced report-discovery freedom
- governed execution trace

## Live-Promotion Status

This slice is implemented and verified, but not yet force-switched into the general live chat path.

That is intentional.

The next decision is architectural, not technical:

1. whether to enable compiled execution for all first-turn requests immediately
2. or enable it behind a feature flag / controlled rollout

## Next Step

Proceed to:

- Phase 4 Slice 5: semantic intent-to-result validation

After Slice 5, the system will be able to reject:

- grounded but semantically wrong results

before they reach the user.
