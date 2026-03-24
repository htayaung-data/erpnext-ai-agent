# Qwen ERP Phase 5 Enterprise Re-Entry Guardrails (2026-03-24)

Status: active re-entry design  
Scope: define the strict enterprise rules for continuing local Phase 5 work after rollback of the recent heuristic slice  
Decision: no more runtime coding until the remaining metadata and interpretation drift is reconciled against enterprise guardrails

Read together with:

1. [AGENT_RULES.md](/home/deploy/erp-projects/erpai_project1/AGENT_RULES.md)
2. [scripts/check_qwen_enterprise_guardrails.py](/home/deploy/erp-projects/erpai_project1/scripts/check_qwen_enterprise_guardrails.py)

## 1. Why This Document Exists

The local post-`daafea9` branch contains useful Phase 5 direction, but it also contains behavior that is not acceptable as final enterprise implementation:

1. business meaning expressed as token rules
2. follow-up behavior driven by example phrases
3. service/interpreter logic drifting back toward lexical heuristics

The rollback removed the most recent bad slice, but the local branch still needs a clean re-entry plan before more implementation.

## 2. Current Understanding

The correct architecture remains:

1. Qwen proposes
2. compiler enforces
3. validator confirms
4. governed artifacts become the only source of truth for the answer

The product should expose only four user-facing outcomes:

1. `governed_execute`
2. `clarify`
3. `contextual_followup_clarify`
4. `governed_out_of_scope`

This means:

1. covered family requests must execute through governed artifacts
2. ambiguous fresh questions must ask business-language clarification
3. ambiguous follow-ups must clarify against prior context
4. uncovered ERP domains must fall back honestly and politely

## 3. Enterprise Rule: What Is Acceptable

The following are acceptable as enterprise mechanisms:

1. canonical concept registries
2. canonical metric/dimension alias registries
3. governed family/capability registries
4. structured clarification reason contracts
5. structured continuation contracts
6. structural parsers for:
   - document ids
   - absolute dates
   - absolute years
   - explicit numeric limits like `top 7`
7. AI-generated clarification and narrative on top of structured governed inputs

These are allowed because they are:

1. explicit
2. auditable
3. generalizable
4. not phrase-patch driven

## 4. Enterprise Rule: What Is Not Acceptable

The following are not acceptable as final implementation:

1. Python business logic based on `if "term" in text`
2. JSON registries that are just keyword rules moved out of Python
3. follow-up modes detected from example phrases like:
   - `include qty`
   - `how about last year`
   - `show me all time`
4. condition registries built on `tokens_any`, `tokens_all`, `tokens_optional` as the primary interpretation architecture
5. prompts or classifier loops for detecting simple confirmations like `yes`, `sure`, `go ahead`
6. exposing technical failure wording to users

Moving keyword logic from code into JSON does not make it enterprise-grade.

## 5. Registry-by-Registry Decision

### 5.1 [semantic_alias_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/semantic_alias_registry.json)

Decision: keep

Reason:

1. it maps canonical business meaning to governed metrics/dimensions
2. it is concept-level, not query-template-level
3. it is a valid enterprise metadata layer

Constraint:

1. aliases must stay at canonical business-term level
2. do not add full query examples here

### 5.2 [business_ontology.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/business_ontology.json)

Decision: keep only concept ontology portions; redesign follow-up metadata

Keep:

1. `concept_id`
2. concept aliases
3. minimal interaction hints only if they are transitional and not business-meaning critical

Remove or redesign:

1. `follow_up_classes[*].detection_pattern`
2. phrase-example follow-up aliases that encode behavior directly
3. follow-up classes that act as query templates instead of governed transforms

Replacement direction:

1. follow-up modes should be defined as canonical transform ids
2. eligibility should come from continuation contracts and family capability metadata
3. slot filling should come from:
   - alias registry
   - structural parsers
   - prior artifact state

### 5.3 [intent_bias_rules_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/intent_bias_rules_registry.json)

Decision: current schema is not enterprise-clean; redesign before deeper use

Problem:

1. the current rule format is mostly lexical token matching
2. this is effectively a keyword engine in metadata form

Replacement direction:

1. replace with capability/family priors keyed by canonical concepts and artifact context
2. allow only bounded structural predicates, such as:
   - concept present
   - explicit document id present
   - explicit year/date present
   - prior artifact family supports transform
3. do not use open-ended token bags as the main decision model

### 5.4 [clarification_templates_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/clarification_templates_registry.json)

Decision: keep, but narrow

Keep:

1. business-language template wording
2. options text
3. label mapping

Change:

1. templates must be driven only by structured clarification reasons
2. remove product-level prompts like asking whether to "add this capability" to governed scope
3. keep the user experience focused on the current question, not product roadmap prompts

## 6. Runtime Layer Decision

### 6.1 [service.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/service.py)

Allowed responsibilities:

1. orchestration
2. persistence
3. audit payload append
4. route to compiler/runtime/entity-detail/clarification system

Not allowed:

1. business-language follow-up interpretation
2. phrase-based scope detection
3. ad hoc clarification generation from failure text

### 6.2 [followup_interpreter.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/followup_interpreter.py)

Allowed responsibilities:

1. continuation classification using prior grounded context
2. structural extraction:
   - entity ids
   - numeric limits
   - explicit years/dates
3. canonical alias resolution using registries

Not allowed:

1. large domain token sets as the primary semantics engine
2. phrase rules for time/metric/column transformations

### 6.3 [clarification_system.py](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/clarification_system.py)

Allowed responsibilities:

1. translate structured clarification reasons into business-language questions
2. AI-first wording, template fallback

Not allowed:

1. infer business intent from raw failure strings
2. compensate for missing contracts by guessing from free text

## 7. Concrete Re-Entry Sequence

No runtime feature work should resume until these are completed in order.

### Step 1: Metadata cleanup

1. simplify [business_ontology.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/business_ontology.json) to concept ontology only
2. redesign or retire current lexical `follow_up_classes`
3. redesign [intent_bias_rules_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/intent_bias_rules_registry.json) so it is not token-rule based
4. trim [clarification_templates_registry.json](/home/deploy/erp-projects/erpai_project1/impl_factory/03_config/qwen_enterprise_metadata/clarification_templates_registry.json) to reason-driven business wording only

### Step 2: Contract-first implementation

Reintroduce only clean contract surfaces:

1. `GovernedScopeDecisionContract`
2. `ClarificationReasonContract`
3. `ArtifactContinuationContract`

Rules:

1. contracts must be populated from structured inputs
2. contracts must not parse business meaning from phrase bags

### Step 3: Interpreter rebuild

1. fresh query scope resolution uses:
   - ontology concepts
   - alias registry
   - governed family registry
2. follow-up interpretation uses:
   - prior artifact continuation
   - structural parsers
   - canonical metric/dimension aliases
3. clarification happens only when the system lacks a required slot

### Step 4: Only then fix business gaps

After the cleanup above, address the remaining user-facing gaps:

1. item-specific monthly trend correctness
2. quantity-follow-up over prior artifact
3. delivery-status enrichment in entity drilldown
4. better out-of-scope fallback coverage

## 8. Acceptance Before More Coding

Before resuming runtime implementation, the branch should satisfy:

1. no new keyword bags added in Python
2. no new token-rule registries added in JSON
3. all remaining semantic meaning expressed through:
   - concepts
   - canonical aliases
   - family capabilities
   - continuation state
   - structural parsers

## 9. Immediate Next Action

The next coding slice should be:

1. metadata cleanup only
2. no service/runtime behavior changes yet
3. after cleanup, review the resulting registry shapes before reintroducing contracts

This is the cleanest way to avoid another expensive drift cycle.
