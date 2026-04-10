# Qwen Chat Financial Summary Runtime Boundary

Status: active first-wave runtime boundary  
Audience: AI/ML, backend, governance maintainers  
Goal: define the exact production boundary for the first `financial_summary` runtime slice

## 1. Current Runtime Status

`financial_summary` is no longer purely legacy-only.

It now has a bounded first-wave semantic runtime slice with these rules:

1. semantic decision happens before legacy fallback
2. supported outcomes are `normalize_intent`, `clarify`, or `no_decision`
3. `execute_composite` is not active in this first wave
4. unsupported or multi-domain cases must not be guessed into a narrower target

This is an intentionally partial migration.

## 2. Supported Normalize Targets

The current runtime slice may normalize `financial_summary` into these governed intents only:

1. `financial_statement`
2. `aging_analysis`
3. `inventory_summary`
4. `product_performance`

### 2.1 Normalization Conditions

Normalization is allowed only when:

1. exactly one summary domain is resolved
2. the summary focus is governed and sufficient for a safe target
3. a governed normalization rule exists in `financial_summary_resolution_registry.json`

### 2.2 First-Wave Examples

Examples that may normalize:

1. payable + outstanding amount -> `aging_analysis`
2. receivable + outstanding amount -> `aging_analysis`
3. statement + statement view -> `financial_statement`
4. inventory + value snapshot -> `inventory_summary`
5. product profitability + profitability snapshot -> `product_performance`

## 3. Supported Clarify Outcomes

The current runtime slice may clarify only through governed clarification rules and governed clarification templates.

Currently active clarification paths:

1. `financial_summary_domain_clarification`
2. `financial_summary_sales_scope_clarification`
3. `financial_summary_focus_clarification`
4. `financial_summary_multi_domain_clarification`

### 3.1 Clarify Rules

Clarification is allowed when:

1. no governed summary domain is resolved yet
2. `sales` is the single resolved domain and no approved first-wave normalize target exists
3. a domain requiring explicit focus is resolved, but the focus is still missing
4. multiple governed summary domains are resolved and first-wave runtime still does not execute cross-domain summary behavior

### 3.2 Fallback Rule

When one of these governed clarification paths is returned:

1. the semantic contract emits `blocks_legacy_fallback = true`
2. compiler preserves that signal in clarification details
3. `fresh_query_interpreter.py` must not re-enter deterministic `family_tool_surface` fallback

This is the current enterprise protection against accidental lexical re-steering.

## 4. Explicitly Unsupported In First Wave

The following are intentionally not implemented in runtime yet:

1. cross-domain composite execution
2. sales-summary normalization
3. composite-scope clarification

If a request falls into one of those categories, the first-wave semantic resolver must not fake a decision.

Current rule:

1. return `None`
2. let the existing broader path continue
3. do not widen the semantic runtime slice by guesswork

## 5. Enterprise Constraints

The current runtime boundary must preserve these rules:

1. no raw message keyword routing
2. no phrase-to-report forcing
3. no single-case runtime patching
4. no composite execution without a governed composite plan match
5. no sales-summary normalization until an approved target exists

## 6. Ownership Boundary

### 6.1 Governed Metadata Owns

These are metadata-owned now:

1. domain rules
2. metric-family rules
3. focus rules
4. grain rules
5. normalization rules
6. clarification rules
7. clarification prompts and suggested options

### 6.2 Runtime Code Still Owns

These remain acceptable orchestration logic in code:

1. calling the resolver
2. choosing normalize vs clarify vs no decision from resolved metadata outcomes
3. carrying the `blocks_legacy_fallback` contract signal
4. preserving the no-widening rule for unsupported first-wave cases

This is normal orchestration logic, not business routing by keywords.

## 7. Next Safe Expansion

The next runtime expansion is allowed only after this boundary remains stable.

Safe next candidates:

1. no automatic expansion by default
2. design-first review for any second composite profile
3. design-first review for any widened cross-domain signal model

Unsafe next candidates for now:

1. sales normalization
2. generic composite execution beyond `working_capital_health`
3. `financial_summary_composite_scope_clarification` without a new governed design checkpoint
4. widening the resolver to guess broad summaries into narrow targets

Current checkpoint:

1. first-wave normalize-and-clarify runtime remains intact
2. second-wave runtime now allows exactly one structured composite execution path:
   `receivable` + `payable` + `cross_domain_health` -> `working_capital_health`
3. further expansion should stop here unless a new design checkpoint explicitly approves it

Historical checkpoint:

1. [QWEN_CHAT_FINANCIAL_SUMMARY_SECOND_WAVE_CHECKPOINT.md](/home/deploy/erp-projects/erpai_project1/impl_factory/05_custom_logic/custom_app/ai_assistant_ui/ai_assistant_ui/qwen_chat/docs/archive/QWEN_CHAT_FINANCIAL_SUMMARY_SECOND_WAVE_CHECKPOINT.md)

## 8. Review Rule

Any future change to `financial_summary` runtime must answer these questions explicitly:

1. is this metadata-owned or orchestration-owned?
2. does this widen the first-wave boundary?
3. does this introduce any lexical routing or user-phrase dependence?
4. does this add a new clarify path without governed metadata?
5. does this bypass `blocks_legacy_fallback` protection?

If the answer to any unsafe condition is yes, the change should stop for review.
