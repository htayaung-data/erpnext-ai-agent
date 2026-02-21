# V7 Runtime Guardrails (Phase 0 Contract-as-Code)

Version: 1.0  
Effective date: 2026-02-21

## Purpose
Enforce non-negotiable V7 runtime constraints with deterministic static checks before merge/deploy.

## Scope
Guardrails apply to:
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7/**`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/llm/**`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/tools/**`

## Hard Rules
1. No keyword/phrase-list routing or scoring constants in runtime core modules.
2. No legacy runtime imports from `v2`, `v3`, `tools.report_qa`, or `v7.engine_mode`.
3. No legacy runtime paths: `ai_core/v2`, `ai_core/v3`, `ai_core/tools/report_qa.py`, `ai_core/v7/engine_mode.py`.
4. No `*.bak` or `*.bak.*` files in repository.
5. Tool registry must be pinned to V7 dispatcher import.
6. Alias dictionaries are permitted only in dedicated ontology normalization module.

## Enforcement Script
- Script: `scripts/check_v7_contract_guardrails.py`
- Run from repository root:

```bash
python3 scripts/check_v7_contract_guardrails.py --root .
```

## Expected Output
- Pass: `V7 contract guardrails: PASS`
- Fail: `V7 contract guardrails: FAILED` with exact file:line violations.

## CI Integration
Minimum CI gate:

```bash
python3 scripts/check_v7_contract_guardrails.py --root .
python3 -m py_compile $(find impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/ai_core/v7 -name '*.py')
```

Any non-zero exit code blocks promotion.
