# Qwen ERP Phase 4B Slice 8 Family Tool Surface Note (2026-03-22)

Status: completed

## Purpose

Slice 4B.8 tightens the runtime-side tool surface so Qwen-Agent no longer treats every non-compiled read as open-ended raw report discovery when a governed business family route is already available.

This slice preserves the enterprise boundary:

- Qwen-Agent proposes and executes within a smaller governed tool surface
- metadata defines the family routes
- runtime policy enforces the allowed report set
- compiler and validator governance remain unchanged

## Implemented

### 1. Governed family tool metadata

The shared family registry now carries runtime-facing family tool hints:

- `agent_tool_id`
- `agent_prompt_hint`
- `routing_hints.ontology_concepts`
- `routing_hints.intent_markers`

Updated metadata:

- `impl_factory/03_config/qwen_enterprise_metadata/report_family_registry.json`

### 2. Family tool surface contract

A new governed contract now represents the runtime-facing family tool surface:

- `FamilyToolSurfaceContract`

It records:

- candidate family ids
- preferred high-level family tool ids
- allowed report names
- whether report discovery is allowed
- the family entries sent to runtime

Updated contract file:

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/contracts.py`

### 3. Deterministic family tool surface builder

A new deterministic ERP-side builder now creates family tool surfaces from governed metadata and ontology matches:

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/family_tool_surface.py`

The builder does not call the model. It uses:

- ontology concept detection
- family routing hints
- family report metadata

### 4. Runtime payload and enforcement

The runtime chat payload now accepts `family_tool_context`, and the runtime uses it in two places:

1. system prompt policy
2. tool gateway enforcement

Runtime changes:

- `experimental/qwen_agent_runtime/app/schemas.py`
- `experimental/qwen_agent_runtime/app/qwen_agent_engine.py`
- `experimental/qwen_agent_runtime/app/tool_gateway_policy.py`
- `experimental/qwen_agent_runtime/app/service.py`

Key runtime behavior:

- when family routing is active, the prompt explicitly prefers family routes over raw report discovery
- the tool gateway can block `erp_fac-report_list`
- the tool gateway restricts report calls to the family-approved report names
- runtime failure responses now preserve routing/tool metadata for auditability

### 5. ERP service integration

The live legacy read-only service path now:

- builds a family tool surface before runtime invocation
- persists that contract into the session audit trail
- passes the runtime payload onward as `family_tool_context`

Updated ERP files:

- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/runtime_client.py`
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/metadata.py`
- `experimental/qwen_agent_runtime/app/report_registry.py`

## Verification

Verified successfully:

1. `python3 -m py_compile` on all touched ERP/runtime modules
2. JSON validation of `report_family_registry.json`
3. runtime image rebuild and restart
4. backend restart
5. deterministic family tool surface probe:
   - `run_phase4b_family_tool_surface_probe`
6. live legacy-path smoke:
   - `run_phase4b_family_tool_surface_smoke`
7. post-4B.8 compiled-path regression:
   - `run_first_turn_regression_suite` on payable aging and AR/AP working-capital health

## Verified Outcome

The deterministic probe now maps representative business requests into governed family surfaces:

- P&L -> `financial_statement`
- payable summary -> `aging`
- top customers by revenue -> `ranking_analytics`
- monthly sales trend -> `trend_analytics`
- product performance -> `product_profitability`

The live legacy-path smoke confirmed:

- family tool surface contract persisted in the ERP session
- runtime agent meta marked family routing active
- runtime report discovery stayed off
- verified legacy ranking request completed through:
  - `erp_fac-report_requirements`
  - `erp_fac-generate_report`
- no `erp_fac-report_list` call was used in that governed legacy-path smoke

The compiled first-turn path also continued to pass after these changes.

## Operational Note

Slice 4B.8 does **not** mean every legacy family route is now fully equivalent to the compiled family path.

Current observed reality:

- legacy `ranking_analytics` routing is verified and working well
- some legacy routes such as `financial_statement`, `aging`, and `trend_analytics` still benefit from stronger requirements-first handling
- compiled execution remains the preferred enterprise path for those richer routes

That is acceptable for this slice because 4B.8 owns:

- reduced family tool surface
- family routing policy
- governed runtime narrowing

It does not replace the compiled path or remove the need for family-based evaluation and latency/quality tracking.

## Next Step

The next step is Slice 4B.9:

- family-based evaluation datasets
- latency metrics by family
- semantic pass/fallback monitoring by family
- rollout tracking by family
