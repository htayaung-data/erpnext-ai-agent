# AGENT_RULES

Status: non-negotiable repository operating rules for AI implementation sessions  
Scope: all future work on the Qwen ERP assistant and related governance/runtime code  
Priority: if any plan, prompt, or note conflicts with this file, this file wins

## 1. Required Read Order

Before making any code change, every implementation session must read these in order:

1. [AGENT_RULES.md](/home/deploy/erp-projects/erpai_project1/AGENT_RULES.md)
2. [qwen_erp_phase5_enterprise_reentry_guardrails_2026-03-24.md](/home/deploy/erp-projects/erpai_project1/impl_factory/00_governance/qwen_erp_phase5_enterprise_reentry_guardrails_2026-03-24.md)
3. [qwen_erp_phase5_reconciled_implementation_plan_2026-03-24.md](/home/deploy/erp-projects/erpai_project1/impl_factory/00_governance/qwen_erp_phase5_reconciled_implementation_plan_2026-03-24.md)

## 2. Non-Negotiable Architecture

The assistant must follow this enterprise rule:

1. Qwen proposes
2. compiler enforces
3. validator confirms
4. governed artifacts are the only source of truth for user-visible answers

The assistant must expose only these user-facing outcomes:

1. `governed_execute`
2. `clarify`
3. `contextual_followup_clarify`
4. `governed_out_of_scope`

## 3. Absolute Do-Not-Do Rules

Do not implement business meaning with:

1. Python checks like `if "term" in text`
2. regex bags of business words as the primary routing logic
3. JSON token engines using fields like:
   - `tokens_any`
   - `tokens_all`
   - `tokens_optional`
   - `tokens_required`
   - `tokens_excluded`
4. example-phrase follow-up rules like:
   - `include qty`
   - `how about last year`
   - `show me all time`
5. confirmation detection from lexical examples like:
   - `yes`
   - `sure`
   - `go ahead`
6. case-by-case phrase patches to fix a browser example
7. user-visible technical leakage such as:
   - capability ids
   - raw compiler diagnostics
   - raw internal exception text
   - “grounded ERP lookup failed” for understandable user requests

Moving keyword logic from Python into JSON does not make it enterprise-grade.

## 4. Allowed Enterprise Mechanisms

Business understanding may be expressed only through:

1. governed family/capability registries
2. ontology concepts
3. canonical semantic alias registries
4. structured continuation contracts
5. structured clarification reason contracts
6. structural parsers for:
   - document ids
   - explicit dates
   - explicit years
   - explicit numeric limits
7. AI-generated wording from structured governed inputs

## 5. Required Workflow

For every implementation slice:

1. Read the required docs above.
2. State which files are the source of truth.
3. Explain the intended change in architecture terms, not example phrases.
4. Run the guardrail audit before editing.
5. Make the smallest clean change.
6. Run the guardrail audit again after editing.
7. Compile or test the touched code.
8. Summarize whether any residual drift remains.

## 6. Stop Conditions

Stop implementation immediately if any of these occur:

1. the intended fix starts depending on lexical query phrases
2. a registry starts becoming a keyword engine
3. service orchestration starts doing business interpretation
4. clarification is being generated from failure text instead of structured reasons
5. the only way to fix something seems to be “just special-case this query”

When any stop condition occurs:

1. do not continue coding
2. document the drift
3. propose a contract/registry/continuation-based alternative first

## 7. Required Audit Command

Run this before and after runtime or metadata changes:

```bash
python3 scripts/check_qwen_enterprise_guardrails.py
```

If it fails, do not describe the implementation as enterprise-clean.

## 8. Scope Rule

It is acceptable that not all ERP domains are covered yet.

For uncovered domains:

1. do not hallucinate
2. do not reuse unrelated prior artifacts
3. do not reject technically
4. respond with polite governed out-of-scope fallback

## 9. Follow-Up Rule

Follow-ups must be resolved from:

1. prior artifact family
2. prior entity focus
3. prior metric
4. prior dimensions
5. prior time scope
6. prior presentation shape
7. structural parsers
8. canonical alias registries

Not from example phrases alone.

## 10. Documentation Rule

If new governance is introduced, update:

1. [AGENT_RULES.md](/home/deploy/erp-projects/erpai_project1/AGENT_RULES.md) if the rule is permanent
2. [qwen_erp_phase5_enterprise_reentry_guardrails_2026-03-24.md](/home/deploy/erp-projects/erpai_project1/impl_factory/00_governance/qwen_erp_phase5_enterprise_reentry_guardrails_2026-03-24.md) if the rule affects Phase 5 implementation behavior
