# Qwen ERP Phase 4 Slice 3 Model Proposal Integration Note (2026-03-22)

Status: implemented and runtime-boundary hardened  
Scope: Phase 4 Slice 3 for fresh-query advisory proposal generation

## Purpose

This slice adds the governed, typed model-proposal layer for first-turn business requests.

The design rule remains:

- `Qwen-Agent proposes`
- `compiler enforces`

The proposal output remains advisory only in this slice.

Live chat execution is not switched to compiled execution yet.

## What Was Implemented

### Runtime Side

Added typed fresh-query interpretation support:

- `experimental/qwen_agent_runtime/app/schemas.py`
- `experimental/qwen_agent_runtime/app/semantic_fresh_query_engine.py`
- `experimental/qwen_agent_runtime/app/service.py`
- `experimental/qwen_agent_runtime/app/main.py`
- `experimental/qwen_agent_runtime/app/settings.py`

Key additions:

1. `FreshQueryInterpretRequest`
2. `FreshQueryInterpretation`
3. `FreshQueryInterpretResponse`
4. `POST /interpret-fresh-query`
5. retry/backoff and JSON-repair behavior for fresh-query proposal generation
6. explicit contract rules:
   - closed-set intent class only
   - advisory candidate reports only
   - no company burden in model output

### ERP Side

Added governed fresh-query interpretation and proposal-to-compiler wiring:

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/runtime_client.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/fresh_query_interpreter.py`

Key additions:

1. runtime client call for `/interpret-fresh-query`
2. governed interpretation context builder from enterprise metadata
3. ERP-side payload validation and canonicalization
4. confidence threshold handling
5. advisory `proposal -> compile` helper path
6. deterministic selftests for validation and compiler handoff

## Verification

### Deterministic Verification

Passed:

- `python3 -m compileall ...`
- `bench execute ai_assistant_ui.qwen_chat.fresh_query_interpreter.run_phase4_fresh_query_interpreter_selftests`

The deterministic selftests verified:

1. valid governed payload is accepted
2. unsupported dimensions are rejected
3. `company` is stripped from model-proposed filters
4. accepted proposal compiles into:
   - `accounts_payable_read`
   - `Accounts Payable Summary`
   - compiler-injected single-company filter
   - compiler-injected report date

### Live Advisory Endpoint Verification

A direct host-to-runtime call to `/interpret-fresh-query` returned a valid governed payable proposal:

- intent class resolved to `financial_summary`
- capability candidate resolved to `accounts_payable_read`
- advisory report candidates returned
- `report_date` extracted
- company remained absent from model output

## Runtime-Boundary Hardening Outcome

The remaining Slice 3 operational issue was traced to:

1. fresh-query provider calls sharing an overly tight 45-second runtime timeout
2. ERP backend traffic reaching the runtime through the host bridge instead of a shared container-network alias

Hardening applied:

1. added `SEMANTIC_FRESH_QUERY_TIMEOUT_SECONDS`
2. kept fresh-query timeout separately configurable from normal chat timeout
3. attached the runtime to the ERP Docker network
4. switched ERP runtime base URL to the shared alias `http://qwen-agent-runtime:8010`
5. added site-level `qwen_agent_runtime_fresh_query_timeout`

Result:

- backend-container-to-runtime advisory calls now complete successfully
- the runtime boundary is now considered hardened enough for continued Phase 4 work

## Why Live Chat Was Still Not Switched Yet

This slice intentionally keeps the proposal output advisory only.

That preserves enterprise safety while:

1. validating the proposal contract
2. validating compiler handoff
3. avoiding premature coupling to the live chat path before compiled execution exists

## Verification Summary

Passed:

1. deterministic selftests for governed payload validation and compiler handoff
2. direct host-to-runtime `/interpret-fresh-query` verification
3. ERP-side `proposal -> compiler` smoke for payable
4. broader advisory smoke pack covering:
   - payable summary -> `execute`
   - analysis-style payable request -> `execute`
   - top customers by revenue -> `clarify`
   - monthly sales trend by region -> `clarify`

These results show the intended Phase 4 behavior:

- valid, defaultable first-turn business requests can compile to execute
- underspecified first-turn requests compile to clarify before runtime execution

## Next Step

Proceed to:

- Phase 4 Slice 4: compiled execution path
