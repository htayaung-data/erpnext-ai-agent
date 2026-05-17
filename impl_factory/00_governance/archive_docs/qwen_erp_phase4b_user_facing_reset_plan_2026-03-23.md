# Qwen ERP Phase 4B User-Facing Reset Plan (2026-03-23)

Status: planned  
Scope: redesign the user-facing layer above the governed Phase 4B core without weakening compiler, adapter, or validator governance  
Goal: preserve enterprise correctness while restoring natural Qwen-Agent behavior, business insight quality, conversational clarification, and drilldown continuity.

## 1. Why This Reset Exists

Phase 4 and Phase 4B solved the hardest enterprise problems:

1. unsafe fresh-query execution
2. uncontrolled report selection
3. weak first-turn correctness
4. lack of canonical business-family normalization
5. missing semantic validation

However, recent browser validation and direct product feedback show a new problem:

- the system is now safer and more deterministic
- but the visible assistant experience has become too rigid, technical, and robotic

The current risk is no longer mainly incorrect data retrieval.

The current risk is:

1. governance becoming too visible to the user
2. deterministic rendering replacing natural business explanation
3. technical clarification leaking internal compiler reasoning
4. follow-up turns feeling stateless even when grounded context exists
5. drilldown questions failing because the system knows report families better than business entities

This reset exists to fix the user-facing layer without discarding the governed foundation.

## 2. Strategic Decision

The current direction should be:

- keep the governed engine
- simplify the visible cabin

Meaning:

1. keep deterministic:
   - compiler routing
   - family/adaptor selection
   - invariant injection
   - normalized artifacts
   - validation
   - audit
2. move back to Qwen-Agent behavior:
   - final narrative
   - business insight phrasing
   - user-friendly clarification
   - contextual follow-up interpretation
   - entity drilldown conversation flow

The governing principle is:

- `governed data, natural narrative`

## 3. Alignment With Qwen Consultation

This reset plan aligns with the latest Qwen guidance:

1. `compiler / adapter / validator` remain the enterprise core
2. deterministic rendering should not remain the primary user-facing answer style
3. the runtime Qwen-Agent should generate the final answer from governed artifacts
4. clarification should be translated into business language
5. follow-up behavior should use semantic thread context, not only fresh compilation
6. generic entity detail should become a first-class governed drilldown path

## 4. Workstreams

### 4.1 Workstream R1: Natural Narrative Layer

Purpose:

- make the assistant sound like a capable ERP consultant again while staying grounded in normalized artifacts

Main idea:

- deterministic family rendering should produce support blocks and canonical data structure
- Qwen-Agent should generate the final answer text from governed artifacts

Required behavior:

1. the final answer must be generated from normalized family or composite artifacts only
2. the agent must not invent metrics or external facts
3. the assistant may produce:
   - direct answer
   - highlight
   - implication
   - recommendation when grounded and appropriate

File responsibilities:

1. [service.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py)
   - switch primary visible answer path from deterministic rendering to narrative orchestration
   - decide when to call narrative generation vs. direct structured fallback
2. [family_rendering.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/family_rendering.py)
   - keep canonical support blocks
   - stop acting as the full visible answer voice
3. [contracts.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/contracts.py)
   - add narrative policy / answer style contract fields
4. new file: `artifact_narrative.py`
   - build runtime prompts and grounded narrative payloads from family/composite artifacts
   - keep prompt logic out of service orchestration
5. runtime integration files as needed:
   - [runtime_client.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/runtime_client.py)
   - runtime-side Qwen orchestration only if the current prompt surface needs dedicated narrative support

Success criteria:

1. the user sees natural answers first, not rigid renderer output first
2. the answer remains grounded in governed artifacts
3. the assistant feels more like a consultant than a report printer

### 4.2 Workstream R2: Human Clarification Translation

Purpose:

- ensure internal compiler ambiguity becomes business-language clarification

Required behavior:

1. never expose messages such as:
   - `Ambiguous capability candidates: ...`
2. instead ask questions such as:
   - `Which area would you like me to analyze: AR/AP, cash flow, profitability, or inventory?`
   - `Would you like to see this for last month, this quarter, or all time?`

File responsibilities:

1. [contracts.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/contracts.py)
   - formalize a `ClarificationSignalContract` or equivalent user-facing clarification payload
   - separate user-visible fields from internal audit-only fields
2. [fresh_query_interpreter.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/fresh_query_interpreter.py)
   - emit structured clarification reasons instead of user-visible technical strings
3. [service.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py)
   - route clarification through a user-facing translation layer
4. new file: `clarification_translation.py`
   - map governed ambiguity signals to business-language questions and suggested options
5. optional UI wiring later:
   - clarification options may eventually become chips/buttons, but that is not required for backend completion

Success criteria:

1. the user no longer sees internal capability or contract labels
2. clarification remains precise while sounding conversational
3. audit still retains the underlying internal ambiguity reasons

### 4.3 Workstream R3: Response Policy By Intent

Purpose:

- make answer shape match business intent instead of always returning the same structured style

Required policy:

1. simple factual question:
   - short direct answer
   - optional highlight
2. analysis question:
   - direct answer
   - key insight
   - recommendation / suggested action when grounded
3. statement question:
   - summary
   - notable line items
   - implication
4. follow-up refinement:
   - preserve previous context
   - behave conversationally
   - avoid re-dumping the full table unless needed

File responsibilities:

1. [contracts.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/contracts.py)
   - add explicit answer-style enum / policy mapping fields
2. [semantic_interpreter.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/semantic_interpreter.py)
   - expose user-intent hints useful for answer policy selection
3. new file: `response_policy.py`
   - determine answer style from intent class, artifact family, and follow-up mode
4. [artifact_narrative.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/artifact_narrative.py)
   - consume policy and compose grounded narrative prompts accordingly
5. [service.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py)
   - apply policy consistently across fresh-query, follow-up, and composite paths

Success criteria:

1. statement requests no longer look like ranking answers
2. analysis requests include grounded insight
3. simple questions answer directly and briefly
4. follow-up refinements sound like a continuing conversation

### 4.4 Workstream R4: Richer Follow-Up Context

Purpose:

- make short same-session turns operate over the prior semantic/business artifact rather than being recompiled blindly

Required behavior:

1. support natural refinements such as:
   - `how about all the time`
   - `show me with their amount`
   - `any recommendation or insights?`
   - `top 5 instead`
2. preserve:
   - previous family
   - previous filters
   - previous metric
   - previous columns
   - previous entity
   - previous answer style where relevant

File responsibilities:

1. [followup_interpreter.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/followup_interpreter.py)
   - strengthen semantic thread interpretation over prior grounded artifact metadata
2. [family_followup.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/family_followup.py)
   - keep family-specific local refinement logic bounded and artifact-aware
3. [contracts.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/contracts.py)
   - extend grounded turn context with artifact family, filters, metric, top_n, selected entity, and answer-style metadata
4. [service.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py)
   - orchestrate follow-up path priority: artifact-aware follow-up first, fresh compilation second
5. [semantic_interpreter.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/semantic_interpreter.py)
   - improve follow-up self-contained detection for short contextual turns

Success criteria:

1. `how about all the time` updates the previous time scope instead of getting stuck
2. `any recommendation or insights?` produces contextual analysis from the prior artifact
3. short refinements stop drifting into unrelated families

### 4.5 Workstream R5: Entity Detail and Drilldown

Purpose:

- support invoice/customer/supplier/item detail and history follow-ups as a governed generic operation

Required behavior:

1. detect entity identifiers and business entities in follow-up turns
2. support entity detail for:
   - invoice
   - customer
   - supplier
   - item
3. support drilldown chain:
   - summary -> entity detail -> history / related documents

File responsibilities:

1. [business_ontology.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/business_ontology.json)
   - expand governed entity classes and identifier patterns
2. [capability_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/capability_registry.json)
   - add governed entity detail capability entries
3. [report_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/report_registry.json)
   - define direct-query or document-backed governed entity detail paths
4. new file: `entity_detail.py`
   - execute normalized detail retrieval and basic related-history retrieval
5. [governed_report_executor.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/governed_report_executor.py)
   - support reusable direct entity detail execution under policy
6. [service.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py)
   - wire entity-detail follow-up routing into the live chat path

Success criteria:

1. `give me details of ACC-SINV-2026-00118` resolves into governed invoice detail
2. supplier detail/history follow-ups stay on the selected supplier entity
3. drilldown questions stop collapsing back into unrelated summaries

## 5. Recommended Implementation Order

The safest build order is:

1. Workstream R2: human clarification translation
2. Workstream R3: response policy by intent
3. Workstream R1: natural narrative layer
4. Workstream R4: richer follow-up context
5. Workstream R5: entity detail and drilldown

Reason for this order:

1. clarification and answer policy define how the user-facing layer should behave
2. natural narrative should be built on top of explicit policy, not ad hoc prompt changes
3. richer follow-up context should be upgraded before drilldown so conversational continuity becomes stable
4. entity detail is most effective once the conversation layer can preserve selected entity context

## 6. What We Are Intentionally Not Changing

This reset should not:

1. remove compiler governance
2. remove family adapters
3. remove semantic validation
4. revert to uncontrolled raw-agent report discovery
5. replace contracts with prompt-only behavior

This is a user-facing reset, not a safety rollback.

## 7. Exit Criteria

The user-facing reset should only be considered successful when:

1. fresh first-turn answers remain grounded and enterprise-safe
2. clarification is always business-language and never exposes compiler internals
3. simple factual requests answer directly without unnecessary verbosity
4. analysis requests include grounded insight and recommendations
5. statement requests explain business implications, not only the statement table
6. short same-session follow-ups preserve prior context naturally
7. invoice and entity drilldowns work through governed detail paths
8. browser validation shows the assistant feels materially more natural and useful than the current deterministic presentation-heavy version

## 8. Immediate Next Step

The immediate next step after this note is:

1. implement Workstream R2 and Workstream R3 together
2. define the explicit clarification contract and answer-style policy first
3. then build the natural narrative layer on top of those contracts

That keeps the reset disciplined and prevents a prompt-only patch cycle.
