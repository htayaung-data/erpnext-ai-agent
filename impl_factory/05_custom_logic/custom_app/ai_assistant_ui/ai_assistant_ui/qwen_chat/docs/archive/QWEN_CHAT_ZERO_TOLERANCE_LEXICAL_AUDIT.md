## Qwen Chat Zero-Tolerance Lexical Audit

Date: 2026-04-01

Scope:
- `impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat`
- supporting verification scripts under `scripts/`

Explicit exclusion:
- `sales_console.js` is outside this task and was not touched.

### Executive Summary

The semantic-governed fresh-query interpreter seam has now been corrected:
- raw-message repair for semantic-governed routing was removed from
  [fresh_query_interpreter.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/fresh_query_interpreter.py)
- guardrails were added so that specific anti-pattern cannot quietly return

However, the repo is **not yet zero-tolerance clean**. The audit found multiple remaining runtime paths that still derive business behavior from raw message text or lexical pattern extraction.

That means:
- current direction is correct
- enterprise-grade endpoint has **not** been fully reached yet
- the remaining work should now be handled as an explicit removal program, not incidental cleanup

### Classification Standard

Acceptable:
- registry-backed alias normalization utilities
- language detection
- formatting detection
- AI-output parsing
- test/scenario prompt strings where the prompt itself is the test contract

Not acceptable for final enterprise runtime:
- raw message text changing capability selection
- raw message text changing report selection
- raw message text changing intent class
- raw message text changing time scope
- raw message text changing family routing
- raw message text changing governed follow-up modes without a structured contract layer

### Tier 0 Fixed In This Pass

Removed from semantic-governed validation/runtime:
- raw message ranking repair
- raw message ranking subject inference
- raw message ranking metric inference
- raw message intent mutation during semantic payload validation
- raw message time-scope derivation during semantic payload validation

Files:
- [fresh_query_interpreter.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/fresh_query_interpreter.py)
- [semantic_resolution.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/semantic_resolution.py)
- [check_qwen_enterprise_guardrails.py](/home/deploy/erp-projects/erpai_project1/scripts/check_qwen_enterprise_guardrails.py)

### Tier 1 Remaining High-Severity Runtime Lexical Routing

1. Legacy family routing surface
- File:
  [family_tool_surface.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/family_tool_surface.py)
- Why it is high severity:
  - it scores governed families from raw message concepts and phrase matches
  - it still functions as a lexical routing engine for legacy paths
- Enterprise-grade target:
  - replace with structured family selection inputs only
  - or confine it to explicit legacy-only quarantine with removal plan

2. Family adapter request-hint extraction
- File:
  [family_adapters.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/family_adapters.py)
- Current patterns:
  - raw-message regex for `top N`
  - raw-message metric hint extraction
  - raw-message output column inference
- Why it is high severity:
  - artifact shape is being influenced directly from the user message
  - this is business behavior, not harmless display logic
- Enterprise-grade target:
  - move request-shape hints into structured follow-up/compiled contracts

3. Follow-up interpreter lexical parsing
- File:
  [followup_interpreter.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/followup_interpreter.py)
- Current patterns:
  - regex projection parsing
  - lexical extraction of requested columns
  - concept detection from raw follow-up text
  - metric/dimension selection from raw text
- Why it is high severity:
  - follow-up behavior is a real runtime control surface
  - this file still contains extensive lexical interpretation logic
- Enterprise-grade target:
  - introduce a governed follow-up semantic contract
  - stop using regex/text parsing as the behavior authority

4. Governed report executor prompt parsing
- File:
  [governed_report_executor.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/governed_report_executor.py)
- Current pattern:
  - regex extracting `last/latest/recent/top N` from request text
- Why it is high severity:
  - execution behavior is being influenced from raw prompt text at runtime
- Enterprise-grade target:
  - require limit/sort/count through structured request contracts only

### Tier 2 Medium-Severity Lexical Runtime Dependencies

5. Clarification resolution concept matching
- File:
  [clarification_resolution.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/clarification_resolution.py)
- Concern:
  - clarification option selection still depends partly on ontology detection over raw text
- Why medium:
  - this is less dangerous than report routing, but still behavioral
- Enterprise-grade target:
  - governed clarification response contract with structured option IDs only

6. Boundary and scope concept inference
- Files:
  [boundary_support.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/boundary_support.py)
  [scope_decision_input.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/scope_decision_input.py)
- Concern:
  - out-of-scope and boundary shaping still depend on ontology concept extraction from raw text
- Why medium:
  - these are safety gates, but still runtime behavior from lexical input
- Enterprise-grade target:
  - explicit structured scope-decision inputs produced earlier in the pipeline

7. Legacy deterministic family fallback in interpreter/lane paths
- Files:
  [fresh_query_interpreter.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/fresh_query_interpreter.py)
  [legacy_runtime_lane.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/lanes/legacy_runtime_lane.py)
- Concern:
  - semantic-governed intents are blocked now, but legacy intents still depend on family lexical surface
- Why medium:
  - quarantined better than before, but still not zero-tolerance clean

### Tier 3 Acceptable Utilities, Not Routing Defects

These were found by the scan but are acceptable or lower risk:

1. Alias/ontology utility libraries
- [semantic_aliases.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/semantic_aliases.py)
- [metadata.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/metadata.py)
- Reason:
  - registry-backed normalization support is acceptable if it is not the runtime authority for routing

2. Language/format detection
- [contracts.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/contracts.py)
- [assistant_formatting.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/assistant_formatting.py)
- [reasoning_execution.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/reasoning_execution.py)
- Reason:
  - regex use here is not business routing

3. AI-output parsing
- [clarification_system.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/clarification_system.py)
- Reason:
  - regex use is parsing generated JSON, not routing business meaning

### Architectural Conclusion

We are no longer at the “monolith emergency” stage.
We are now at the “remove lexical authority from runtime” stage.

The next correct program is no longer endless local cleanup.
It is a contract-first redesign:

1. introduce a governed follow-up boundary contract
2. make `followup_interpreter.py` consume that contract instead of inferring business meaning from raw follow-up text
3. keep `family_tool_surface.py` quarantined and non-authoritative
4. treat `family_adapters.py` and `governed_report_executor.py` as lower-priority review items unless fresh evidence shows new risk

### Guardrail Status

The current guardrail now explicitly blocks the semantic-governed interpreter anti-pattern we removed.
It does **not** yet block all remaining Tier 1/Tier 2 lexical runtime seams above.

That broader expansion should happen only after each target seam is redesigned, so the guardrail encodes the new boundary instead of just flagging the old world all at once.

### Bottom Line

Current status:
- semantic-governed fresh-query seam: materially improved
- repo-wide zero-tolerance lexical standard: not yet achieved

This audit confirms the direction is right, but the removal program should now move from ad hoc file-by-file cleanup to the explicit next-wave plan in:

1. [QWEN_CHAT_NEXT_WAVE_PLAN.md](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/QWEN_CHAT_NEXT_WAVE_PLAN.md)
